# JARVIS 통합판 3.0

JARVIS 1의 대화·휴대폰 연동 기능과 2.0의 로컬 명령 우선 처리·대화 저장 방향을 합쳐 다시 구현한 Android Termux 비서입니다. PC 서버 없이 휴대폰에서 실행합니다. AI 대화는 Gemini 또는 Groq의 인터넷 API를 사용합니다.

## 무엇이 달라졌나요?

- 간단한 한국어 명령은 AI 없이 처리합니다. “배터리 알려줘”, “손전등 켜줘”, “3분 타이머”를 바로 쓸 수 있습니다.
- Gemini와 Groq 모두 도구 정의 전달 → 실제 함수 실행 → 결과 전달 → 답변 흐름을 구현했습니다.
- AI 답변 뒤에 실제 도구 처리 결과를 따로 표시합니다. 후속 API 요청이 실패해도 이미 실행한 작업 결과를 보존합니다.
- SQLite에 대화와 타이머를 저장합니다. AI에는 최근 최대 12개 대화 쌍, 합계 최대 24,000자를 전달합니다.
- 장치 명령 실패·권한 오류·시간 초과를 성공으로 표시하지 않습니다. 배터리·Wi-Fi·GPS에 가짜 대체값을 넣지 않습니다.
- 사진은 사용자가 분석을 요청하고 업로드를 확인했을 때 촬영합니다. 작업 종료 시 임시 사진을 삭제합니다.
- Python 3.10 이상 표준 라이브러리만 사용합니다. 별도 pip 패키지나 Google SDK 설치가 필요 없습니다.
- 1의 실행 명령인 `python main.py`와 2의 `python javis.py`를 모두 지원합니다.

2.0에서 공개되지 않은 core 구현을 복구한 것은 아닙니다. 공개된 호출 구조를 참고해 필요한 모듈을 새로 만들었습니다.

## 휴대폰에 설치하기

1. **Termux와 Termux:API Android 앱**을 같은 배포 출처에서 설치합니다. 처음 설치한다면 F-Droid의 두 앱을 함께 사용하는 방법이 있습니다. 서로 다른 출처의 앱을 섞으면 서명이 맞지 않을 수 있습니다. [Termux 공식 설치 안내](https://github.com/termux/termux-app#installation)
2. 이 ZIP을 휴대폰의 다운로드 폴더에 저장합니다. 파일명은 `jarvis-integrated.zip`입니다.
3. Termux에서 아래 명령을 순서대로 입력합니다. 저장소 권한 요청이 나오면 허용합니다.

```bash
termux-setup-storage
pkg update -y
pkg install -y unzip nano
unzip ~/storage/downloads/jarvis-integrated.zip -d ~
cd ~/jarvis-integrated
bash setup_termux.sh
nano .env
```

이전 설치의 같은 폴더가 있다면 먼저 이름을 바꿔 보관하고 새 폴더로 설치하세요. 기존 프로젝트나 대화 DB를 덮어쓰지 않아도 됩니다.

4. `.env`에서 사용할 API 키 한 가지를 입력합니다.

```dotenv
AI_PROVIDER=auto
GEMINI_API_KEY=여기에_본인_Gemini_키
GROQ_API_KEY=
GEMINI_MODEL=auto
```

Groq를 쓰려면 Gemini 키를 비우고 `GROQ_API_KEY`에 입력하면 됩니다. 두 키를 모두 설정한 경우 `auto`는 Gemini를 선택합니다. `AI_PROVIDER=groq`로 Groq를 직접 선택할 수도 있습니다. 사진 분석에는 별도로 Gemini 키가 필요합니다.

nano에서는 **Ctrl+O → Enter → Ctrl+X**로 저장하고 나옵니다. API 키는 채팅이나 공개 저장소에 붙여 넣지 마세요.

5. 실행합니다.

```bash
bash start.sh
```

API 키가 없어도 로컬 장치 명령과 타이머는 사용할 수 있습니다. Android 설정에서 사용하는 기능에 맞춰 Termux:API의 마이크·카메라·위치·알림 권한을 허용하세요. 로컬 명령도 해당 장치 권한은 필요합니다.

## 자주 쓰는 기능

| 입력 | 동작 |
|---|---|
| 배터리 알려줘 | 실제 배터리 상태 조회 |
| 손전등 켜줘 / 손전등 꺼줘 | 손전등 제어 |
| 와이파이 상태 | 실제 Wi-Fi 정보 조회 |
| 현재 날씨 알려줘 | GPS 위치의 Open-Meteo 날씨 조회 |
| 3분 타이머 | 타이머 등록 |
| 손전등 켜고 배터리도 알려줘 | AI가 필요한 도구를 차례로 호출 |
| /voice | 한 번 음성 입력 |
| /handsfree | 연속 음성 대화, “종료” 또는 Ctrl+C로 돌아가기 |
| /speak | 텍스트 답변 음성 읽기 켜기/끄기 |
| /camera 앞에 뭐가 있는지 설명해줘 | 확인 후 촬영·Gemini 분석 |
| /clipboard get | 클립보드를 화면에 표시 |
| /clipboard set 복사할 내용 | 클립보드에 쓰기 |
| /notify 준비물\|노트북 챙기기 | 휴대폰 알림 게시 |
| /timer 3m 라면 | 이름 있는 타이머 |
| /timers | 타이머 예정 시각과 결과 조회 |
| /cancel 1 | 1번 대기 중 타이머 취소 |
| /play /sdcard/Music/song.mp3 | 지정한 오디오 파일 재생 |
| /stop | 오디오 재생 정지 |
| /search Python | DuckDuckGo Instant Answer 요약 조회 |
| /history | 저장된 최근 대화 보기 |
| /forget | 저장 대화 삭제, 타이머는 유지 |
| /status | API 설정 여부와 장치 연결 진단 |
| /help /exit | 전체 명령 보기 / 종료 |

손전등 사용법을 묻는 문장이나 여러 기능이 섞인 요청은 로컬 단순 명령으로 오인하지 않고 AI에 전달합니다. 이름·말투·장기 기억을 추론해 관리하는 별도 기능은 없으며, 대화 기록을 제한된 범위로 이어서 보내는 방식입니다.

## 실행과 설정

```bash
python javis.py
python main.py --voice
python javis.py --check
python javis.py --version
```

- `GEMINI_MODEL=auto`: 계정에서 조회되는 generateContent 지원 Flash 모델 중 일반 대화용 후보를 선택합니다. 모델별 도구·이미지 지원 여부는 실제 요청에서 확인되며, 오류가 나면 접근 가능한 모델 ID를 직접 지정하세요.
- `GROQ_MODEL`: 기본값 `llama-3.3-70b-versatile`. 계정에서 지원하는 다른 도구 호출 모델로 변경할 수 있습니다.
- `JARVIS_NAME`: 화면 이름.
- `JARVIS_DATA_DIR`: 대화·타이머 저장 폴더. 기본값은 프로젝트 내부 `data`입니다.
- 기존 1의 `JARVIS_MODEL`도 호환합니다. `GEMINI_MODEL`이 있으면 그것이 우선합니다.
- 실행 환경에 이미 설정된 환경변수가 `.env`보다 우선합니다. `.env`는 한 줄에 하나의 KEY=VALUE를 쓰며 변수 치환이나 셸 실행을 하지 않습니다.

데스크톱에서도 Python 3.10 이상으로 텍스트 대화·저장·테스트를 사용할 수 있습니다. 휴대폰 제어와 음성 입출력은 Android Termux:API가 필요하며, Windows에서 가짜로 성공한 것처럼 처리하지 않습니다.

## 저장·전송 범위와 한계

- 일반 AI 대화와 AI 도구 호출 결과는 선택한 AI 서비스로 전송됩니다. 대화는 로컬 DB에 최대 500개 대화 쌍을 저장합니다.
- 로컬 단순 명령의 결과는 대화 기록에는 남지만 AI 문맥에는 자동 포함하지 않습니다. 클립보드 명령과 사진 명령은 대화 DB에 저장하지 않습니다.
- 사진 분석은 촬영 전 전송 확인을 받으며 Gemini에 사진이 전달됩니다. 임시 사진은 성공·실패 시 모두 삭제합니다. 강제 종료나 전원 차단 때까지 삭제를 보장하는 것은 아닙니다.
- 날씨 조회에는 GPS 좌표가 Open-Meteo에, 검색에는 검색어가 DuckDuckGo에 전달됩니다. Android 음성 인식의 네트워크 사용 여부는 선택한 음성 서비스에 따릅니다.
- 검색은 Instant Answer 요약 기능입니다. 일반 웹 검색·최신 뉴스 전체 검색 기능으로 설명하지 않습니다.
- 타이머는 **이 프로그램이 실행 중일 때** 처리합니다. 앱 종료·Android 강제 종료 중에는 울리지 않으며, 다음 실행 때 만료된 타이머를 처리합니다. 한 번에 하나의 JARVIS 프로세스를 실행하세요.
- 알림·진동 성공은 Termux API에 요청이 전달됐다는 뜻입니다. 기기의 무음·알림 차단·배터리 절약 설정 때문에 실제 체감 동작은 달라질 수 있습니다.
- 대화 DB는 암호화되지 않습니다. `/forget`은 논리적인 기록 삭제이며 디스크의 안전한 완전 삭제 기능은 아닙니다.
- 2.0의 원래 DB 구조는 공개되지 않아 자동 이전하지 않습니다. 새 프로젝트 폴더와 새 DB로 시작합니다.

## 문제 해결

| 증상 | 확인할 내용 |
|---|---|
| termux-… 명령이 없음 | `pkg install termux-api`, Termux:API Android 앱도 별도 설치 |
| 장치 명령 시간 초과 | Termux:API 앱·권한·Android 배터리 제한, 위치 요청은 GPS 상태 |
| HTTP 401/403 | API 키와 계정의 모델 접근 권한 |
| HTTP 404 | 접근 가능한 모델 ID 설정, Gemini는 `GEMINI_MODEL=auto` |
| HTTP 429 | 서비스 사용량·요금 한도 확인 후 다시 시도 |
| 음성 인식이 안 됨 | 마이크 권한과 Android 음성 인식 서비스 |
| 음악 파일 접근 실패 | `termux-setup-storage` 실행 및 실제 파일 경로 확인 |

## 개발과 검증

```bash
python -m unittest discover -s tests -v
```

테스트는 API와 휴대폰 명령을 대체해 도구 호출 연결, 오류 처리, 대화 저장, 타이머 복원, 사진 정리 등을 검증합니다. 자세한 실행 결과와 실기기 미검증 항목은 `VALIDATION.txt`를 참고하세요. GitHub Actions 설정도 포함했지만 GitHub에서 실제 실행한 결과는 아닙니다.

```text
javis.py / main.py   실행·대화·음성 흐름
config.py           환경설정
core/ai.py          Gemini·Groq 도구 호출과 사진 분석
core/phone.py       Termux:API 실행
core/tools.py       도구 검증·로컬 명령·날씨·검색
core/memory.py      SQLite 대화·타이머 저장
core/timers.py      만료 타이머 처리
core/http.py        HTTP 연결과 오류 처리
core/ui.py          터미널 표시
tests/              자동 테스트
```

## 참고한 공개 코드와 공식 문서

- [JARVIS 1: NovaSungyu/javis, 0b35bdf](https://github.com/NovaSungyu/javis/tree/0b35bdf1d85f04231e1f9f0736704b03a71a7cdd)
- [JARVIS 2.0: NovaSungyu/javis2, 25abd34](https://github.com/NovaSungyu/javis2/tree/25abd3419f366637bc766d3b10412da775c46fe8)
- [Gemini generateContent](https://aistudio.google.com/api-reference/generate-content)
- [Groq 도구 호출](https://console.groq.com/docs/tool-use/overview)
- [Termux:API 명령 구현](https://github.com/termux/termux-api-package)

통합판은 별도 폴더로 작성했습니다. 원본 GitHub 저장소 변경이나 업로드는 수행하지 않았습니다.

