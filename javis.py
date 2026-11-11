"""Android Termux assistant. Also runs in text-only mode on desktop Python."""
import argparse
import re
import tempfile
from pathlib import Path
from config import Config
from core.ai import AI
from core.errors import JarvisError
from core.http import JsonHTTP
from core.memory import Memory
from core.phone import Phone
from core.timers import TimerService
from core.tools import Tools, local_command, render
from core.ui import UI, safe_text

HELP = """
대화: 평소처럼 입력하세요. 복잡한 장치 요청은 AI 도구 호출로 처리합니다.
바로 실행: 배터리 알려줘 / 와이파이 상태 / 손전등 켜줘 / 3분 타이머

/voice                 한 번 음성 입력
/handsfree             연속 음성 대화 (종료·그만·stop으로 복귀)
/speak                 텍스트 답변의 음성 읽기 켜기/끄기
/status                연결·설정·배터리·Wi-Fi 상태
/battery /wifi         장치 상태 조회
/torch on|off          손전등
/location /weather     GPS 위치 / 현재 날씨
/timer 3m 라면         타이머 (s 초, m 분, h 시간)
/timers                최근 타이머와 처리 결과
/cancel 1              대기 중 타이머 취소
/notify 제목|내용      휴대폰 알림
/toast 메시지          화면 메시지
/vibrate 500           진동 (1~5000ms)
/play /sdcard/Music/a.mp3   로컬 오디오 재생
/stop                  오디오 정지
/search 검색어         DuckDuckGo Instant Answer 요약
/clipboard get         클립보드 읽기 (AI에 전송하지 않음)
/clipboard set 내용    클립보드 쓰기
/camera 질문           촬영·Gemini 분석 (업로드 전 확인)
/history               최근 저장 대화
/forget                저장 대화 삭제 (타이머 유지)
/clear /help /exit     화면 정리 / 도움말 / 종료
"""


class Jarvis:
    def __init__(self, config, phone=None, http=None, ui=None):
        self.config = config
        self.phone, self.http, self.ui = phone or Phone(), http or JsonHTTP(), ui or UI()
        self.memory = Memory(config.data_dir / "javis.db")
        self.tools = Tools(self.phone, self.memory, self.http)
        self.ai = AI(config, self.tools, self.http)
        self.timers = TimerService(self.memory, self.phone, lambda msg: self.ui.say(msg, "TIMER"))
        self.auto_speak = False

    def chat(self, text):
        if len(text) > 12000:
            return "입력이 너무 깁니다. 12,000자 이내로 입력하세요."
        command = local_command(text)
        if command:
            answer = render(self.tools.execute(*command))
            self.memory.add(text, answer, share=False)
            return answer
        reply = self.ai.chat(text, self.memory.recent(shared_only=True))
        answer = reply.display()
        self.memory.add(text, answer, share=reply.ok or bool(reply.actions))
        return answer

    def status(self):
        key = self.config.gemini_key if self.config.provider == "gemini" else self.config.groq_key
        model = (self.ai.selected_gemini or self.config.gemini_model) if self.config.provider == "gemini" else self.config.groq_model
        lines = [f"AI: {self.config.provider} / 모델: {model} / 키: {'설정됨' if key else '없음 (로컬 명령 가능)'}",
                 f"대화 저장: {self.memory.path}",
                 "휴대폰 기능은 Termux:API 앱과 Android 권한이 필요합니다."]
        for name in ("battery", "wifi"):
            lines.append(name + ": " + render(self.tools.execute(name, {})))
        return "\n".join(lines)

    def camera(self, prompt):
        if not self.config.gemini_key:
            return "사진 분석에는 GEMINI_API_KEY가 필요합니다."
        if not self.ui.confirm("카메라로 촬영한 사진을 Gemini에 전송해 분석할까요?"):
            return "사진 분석을 취소했습니다."
        with tempfile.TemporaryDirectory(prefix="jarvis-photo-", dir=self.config.data_dir) as directory:
            path = Path(directory) / "photo.jpg"
            self.phone.photo(path)
            if path.stat().st_size > 10 * 1024 * 1024:
                raise JarvisError("사진이 10MB보다 큽니다.")
            answer = self.ai.describe_photo(path.read_bytes(), prompt or "사진을 설명해줘.")
        return answer

    def speak(self, text):
        try:
            self.phone.speak(text)
        except JarvisError as error:
            self.ui.say(str(error), "음성 출력")

    def voice(self, continuous=False):
        if not self.phone.available("termux-speech-to-text"):
            self.ui.say("음성 인식은 Termux:API 설치와 마이크 권한이 필요합니다.")
            return
        failures = 0
        while True:
            try:
                self.ui.say("듣고 있습니다… (Ctrl+C로 돌아가기)", "음성")
                text = self.phone.listen()
                if not text:
                    failures += 1
                    self.ui.say("인식된 말이 없습니다.")
                    if not continuous or failures >= 3:
                        return
                    continue
                failures = 0
                self.ui.say(text, "YOU")
                if text.strip().rstrip(".!?").lower() in ("종료", "그만", "음성 종료", "exit", "stop"):
                    return
                answer = self.chat(text)
                self.ui.say(answer)
                self.speak(answer)
                if not continuous:
                    return
            except KeyboardInterrupt:
                return
            except JarvisError as error:
                self.ui.say(str(error), "음성 오류")
                return

    def handle(self, text):
        if not text.startswith("/"):
            return self.chat(text)
        command, _, arg = text.partition(" ")
        command, arg = command.lower(), arg.strip()
        if command in ("/exit", "/quit"):
            return None
        if command == "/help":
            return HELP
        if command == "/status":
            return self.status()
        if command == "/clear":
            self.ui.clear()
            return "화면을 정리했습니다. 대화 기억은 유지됩니다."
        if command == "/forget":
            self.memory.clear()
            return "저장 대화를 삭제했습니다. 타이머는 유지됩니다."
        if command == "/history":
            return "\n\n".join(f"YOU: {t['user']}\nJARVIS: {t['assistant']}" for t in self.memory.recent()) or "저장 대화가 없습니다."
        if command == "/speak":
            self.auto_speak = not self.auto_speak
            return "음성 읽기 " + ("켜짐" if self.auto_speak else "꺼짐")
        if command in ("/voice", "/handsfree", "/hf"):
            self.voice(command != "/voice")
            return "음성 입력을 마쳤습니다."
        if command == "/camera":
            return self.camera(arg)
        if command == "/clipboard":
            action, _, content = arg.partition(" ")
            if action == "get" and not content:
                return self.phone.clipboard_get() or "(빈 클립보드)"
            if action == "set" and content:
                if len(content) > 12000:
                    raise JarvisError("클립보드 입력은 12,000자 이내로 입력하세요.")
                return self.phone.clipboard_set(content)
            raise JarvisError("/clipboard get 또는 /clipboard set 내용을 입력하세요.")
        simple = {"/battery": "battery", "/wifi": "wifi", "/location": "location",
                  "/weather": "weather", "/timers": "timers", "/stop": "stop_audio"}
        if command in simple and not arg:
            return render(self.tools.execute(simple[command], {}))
        if command == "/torch" and arg.lower() in ("on", "off"):
            return render(self.tools.execute("torch", {"state": arg.lower() == "on"}))
        if command == "/timer":
            match = re.fullmatch(r"(\d+)(s|m|h|초|분|시간)?(?:\s+(.+))?", arg)
            if not match:
                raise JarvisError("사용법: /timer 3m 라면 (초 s, 분 m, 시간 h)")
            amount = int(match[1]) * {"s": 1, "초": 1, "m": 60, "분": 60, "h": 3600, "시간": 3600}[match[2] or "s"]
            return render(self.tools.execute("timer", {"seconds": amount, "label": match[3] or "타이머"}))
        if command in ("/cancel", "/vibrate") and arg.isascii() and arg.isdigit():
            name, key = ("cancel_timer", "identifier") if command == "/cancel" else ("vibrate", "duration_ms")
            return render(self.tools.execute(name, {key: int(arg)}))
        if command == "/notify":
            title, sep, content = arg.partition("|")
            if not sep:
                raise JarvisError("사용법: /notify 제목|내용")
            return render(self.tools.execute("notification", {"title": title.strip(), "content": content.strip()}))
        if command in ("/toast", "/search", "/play") and arg:
            name, key = {"/toast": ("toast", "text"), "/search": ("search", "query"), "/play": ("play_audio", "path")}[command]
            return render(self.tools.execute(name, {key: arg}))
        return "명령 또는 인자를 확인하세요. /help로 사용법을 볼 수 있습니다."

    def run(self, voice=False):
        self.ui.boot(self.config.name)
        self.timers.start()
        try:
            if voice:
                self.voice(continuous=True)
                return
            while True:
                try:
                    text = input("\nYOU › ").strip()
                    if not text:
                        continue
                    answer = self.handle(text)
                    if answer is None:
                        break
                    self.ui.say(answer, self.config.name)
                    if self.auto_speak and not text.startswith(("/history", "/clipboard")):
                        self.speak(answer)
                except EOFError:
                    break
                except KeyboardInterrupt:
                    self.ui.say("작업을 중단했습니다. 종료하려면 /exit를 입력하세요.")
                except (JarvisError, ValueError) as error:
                    self.ui.say(str(error), "오류")
                except Exception:
                    self.ui.say("예상하지 못한 오류가 발생했습니다. /status로 상태를 확인하세요.", "오류")
        finally:
            self.timers.close()


def main():
    parser = argparse.ArgumentParser(description="JARVIS 통합판 — Android Termux AI 비서")
    parser.add_argument("--voice", "--handsfree", action="store_true", help="연속 음성 모드")
    parser.add_argument("--check", action="store_true", help="설정과 장치 진단 후 종료")
    parser.add_argument("--version", action="version", version="JARVIS Integrated 3.0.0")
    args = parser.parse_args()
    try:
        app = Jarvis(Config.load())
        if args.check:
            print(safe_text(app.status()))
        else:
            app.run(voice=args.voice)
    except (ValueError, OSError) as error:
        print("시작 실패: " + safe_text(error))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
