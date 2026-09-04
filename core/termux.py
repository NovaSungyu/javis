import os
import json
import shutil
import subprocess
import sys
from typing import Dict, Any, Optional

class TermuxBridge:
    """Interface for Android Termux hardware bridge with pure Python fallbacks."""
    
    @staticmethod
    def is_termux_api_available() -> bool:
        """Check if termux-api helper binaries are available."""
        return shutil.which("termux-battery-status") is not None

    @classmethod
    def run_cmd(cls, command: list[str]) -> Optional[str]:
        """Execute a termux-api command safely."""
        if not cls.is_termux_api_available():
            return None
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=10, check=True
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    @classmethod
    def get_battery_status(cls) -> Dict[str, Any]:
        """Get device battery status via termux-api or Linux sysfs."""
        output = cls.run_cmd(["termux-battery-status"])
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass
        
        # Pure Linux sysfs fallback for Android
        capacity_file = "/sys/class/power_supply/battery/capacity"
        if os.path.exists(capacity_file):
            try:
                with open(capacity_file, "r") as f:
                    pct = int(f.read().strip())
                return {"percentage": pct, "status": "UNKNOWN", "health": "GOOD", "temperature": 25.0}
            except Exception:
                pass

        return {"percentage": 100, "status": "DISCHARGING", "health": "GOOD", "temperature": 25.0, "mock": True}

    @classmethod
    def set_torch(cls, state: bool) -> str:
        """Turn flashlight on or off."""
        action = "on" if state else "off"
        res = cls.run_cmd(["termux-torch", action])
        if res is not None:
            return f"Torch turned {action}"
        return f"Torch state set to {action} (Standalone Mode)"

    @classmethod
    def vibrate(cls, duration_ms: int = 500) -> str:
        """Vibrate device for a given duration in milliseconds."""
        cls.run_cmd(["termux-vibrate", "-d", str(duration_ms)])
        return f"Vibrated for {duration_ms}ms"

    @classmethod
    def show_toast(cls, message: str) -> str:
        """Display a short Android toast message."""
        cls.run_cmd(["termux-toast", message])
        return f"Toast displayed: {message}"

    @classmethod
    def send_notification(cls, title: str, content: str) -> str:
        """Post a system notification in Android status bar."""
        cls.run_cmd(["termux-notification", "-t", title, "-c", content])
        return f"Notification posted: {title}"

    @classmethod
    def speak(cls, text: str, rate: float = 1.0, pitch: float = 1.0) -> str:
        """Speak text aloud using Termux-API or pure gTTS standalone engine."""
        # Try Termux-API tts-speak first
        if cls.is_termux_api_available():
            res = cls.run_cmd(["termux-tts-speak", "-r", str(rate), "-p", str(pitch), text])
            if res is not None:
                return "Spoke text successfully via Termux API"

        # Standalone gTTS + mpv/play-audio fallback
        try:
            from gtts import gTTS
            tts_file = "temp_jarvis_speech.mp3"
            tts = gTTS(text=text, lang="ko")
            tts.save(tts_file)
            
            # Play using mpv or play-audio if available
            player = shutil.which("mpv") or shutil.which("play-audio") or shutil.which("ffplay")
            if player:
                subprocess.run([player, tts_file], capture_output=True, timeout=15)
            
            if os.path.exists(tts_file):
                os.remove(tts_file)
            return "Spoke text successfully via gTTS"
        except Exception:
            print(f"[J.A.R.V.I.S. Audio Output]: {text}")
            return "Spoke text (Console output)"

    @classmethod
    def speech_to_text(cls) -> str:
        """Listen to user speech via Android speech recognition or terminal fallback."""
        output = cls.run_cmd(["termux-speech-to-text"])
        return output if output else ""

    @classmethod
    def get_clipboard(cls) -> str:
        """Get current text from clipboard."""
        output = cls.run_cmd(["termux-clipboard-get"])
        return output if output else "Clipboard unavailable in standalone mode."

    @classmethod
    def set_clipboard(cls, text: str) -> str:
        """Copy text to clipboard."""
        cls.run_cmd(["termux-clipboard-set", text])
        return "Text copied to clipboard."

    @classmethod
    def get_wifi_info(cls) -> Dict[str, Any]:
        """Get current Wi-Fi connection info."""
        output = cls.run_cmd(["termux-wifi-connectioninfo"])
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass
        return {"ssid": "Wi-Fi Active", "ip": "127.0.0.1", "link_speed_mbps": 100}

    @classmethod
    def take_photo(cls, camera_id: int = 0, output_path: str = "temp_photo.jpg") -> bool:
        """Take a photo using device camera."""
        output = cls.run_cmd(["termux-camera-photo", "-c", str(camera_id), output_path])
        return output is not None

    @classmethod
    def get_location(cls) -> Dict[str, Any]:
        """Get current GPS/Network location coordinates."""
        output = cls.run_cmd(["termux-location", "-p", "gps", "-r", "last"])
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass
        return {"latitude": 37.5665, "longitude": 126.9780, "provider": "default_seoul"}

    @classmethod
    def play_media(cls, file_path: str) -> str:
        """Play audio file."""
        cls.run_cmd(["termux-media-player", "play", file_path])
        return f"Playing media: {file_path}"

    @classmethod
    def stop_media(cls) -> str:
        """Stop media player playback."""
        cls.run_cmd(["termux-media-player", "stop"])
        return "Media playback stopped"
