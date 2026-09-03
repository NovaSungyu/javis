import json
import shutil
import subprocess
import sys
from typing import Dict, Any, Optional

class TermuxBridge:
    """Interface for Android Termux-API CLI tools."""
    
    @staticmethod
    def is_termux_available() -> bool:
        """Check if termux-api CLI is available in the current environment."""
        return shutil.which("termux-battery-status") is not None

    @classmethod
    def run_cmd(cls, command: list[str]) -> Optional[str]:
        """Execute a termux-api command safely."""
        if not cls.is_termux_available():
            print(f"[Mock System] Executing command: {' '.join(command)}", file=sys.stderr)
            return None
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=10, check=True
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"[Termux Error] Command {' '.join(command)} failed: {e}", file=sys.stderr)
            return None

    @classmethod
    def get_battery_status(cls) -> Dict[str, Any]:
        """Get device battery health, percentage, status, and temperature."""
        output = cls.run_cmd(["termux-battery-status"])
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass
        # Fallback / Mock
        return {"percentage": 100, "status": "DISCHARGING", "health": "GOOD", "temperature": 25.0, "mock": True}

    @classmethod
    def set_torch(cls, state: bool) -> str:
        """Turn flashlight on or off."""
        action = "on" if state else "off"
        cls.run_cmd(["termux-torch", action])
        return f"Torch turned {action}"

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
        """Speak text aloud using Android Text-to-Speech."""
        if not cls.is_termux_available():
            print(f"[JARVIS Speech]: {text}")
            return "Spoke (mock)"
        cls.run_cmd(["termux-tts-speak", "-r", str(rate), "-p", str(pitch), text])
        return "Spoke text successfully"

    @classmethod
    def speech_to_text(cls) -> str:
        """Listen to user speech via Android speech recognition."""
        output = cls.run_cmd(["termux-speech-to-text"])
        return output if output else ""

    @classmethod
    def get_clipboard(cls) -> str:
        """Get current text from clipboard."""
        output = cls.run_cmd(["termux-clipboard-get"])
        return output if output else "Clipboard is empty or unavailable."

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
        return {"ssid": "Unknown/Mock", "ip": "127.0.0.1", "link_speed_mbps": 100}

    @classmethod
    def take_photo(cls, camera_id: int = 0, output_path: str = "temp_photo.jpg") -> bool:
        """Take a photo using device camera (0 for rear, 1 for front)."""
        output = cls.run_cmd(["termux-camera-photo", "-c", str(camera_id), output_path])
        return output is not None or not cls.is_termux_available()

    @classmethod
    def get_location(cls) -> Dict[str, Any]:
        """Get current GPS/Network location coordinates."""
        output = cls.run_cmd(["termux-location", "-p", "gps", "-r", "last"])
        if not output:
            output = cls.run_cmd(["termux-location", "-p", "network", "-r", "last"])
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass
        return {"latitude": 37.5665, "longitude": 126.9780, "provider": "mock_seoul"}

    @classmethod
    def play_media(cls, file_path: str) -> str:
        """Play audio file using Termux media player."""
        cls.run_cmd(["termux-media-player", "play", file_path])
        return f"Playing media: {file_path}"

    @classmethod
    def stop_media(cls) -> str:
        """Stop Termux media player playback."""
        cls.run_cmd(["termux-media-player", "stop"])
        return "Media playback stopped"


