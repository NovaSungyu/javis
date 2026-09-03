import os
import time
import threading
import urllib.parse
import requests
from typing import Dict, Any
from core.termux import TermuxBridge

def get_battery_status() -> str:
    """Get the current battery level, health, charging status, and temperature of the device."""
    info = TermuxBridge.get_battery_status()
    pct = info.get("percentage", "unknown")
    status = info.get("status", "unknown")
    health = info.get("health", "unknown")
    temp = info.get("temperature", "unknown")
    return f"Battery Level: {pct}%, Status: {status}, Health: {health}, Temp: {temp}°C"

def set_flashlight(state: bool) -> str:
    """Turn the phone flashlight/torch on (true) or off (false).
    
    Args:
        state: True to turn flashlight ON, False to turn OFF.
    """
    return TermuxBridge.set_torch(state)

def send_notification(title: str, content: str) -> str:
    """Send an Android system notification to the status bar.
    
    Args:
        title: Notification title
        content: Notification body text
    """
    return TermuxBridge.send_notification(title, content)

def show_toast_message(message: str) -> str:
    """Display a popup toast message on the phone screen.
    
    Args:
        message: Text to display in toast
    """
    return TermuxBridge.show_toast(message)

def read_clipboard() -> str:
    """Read the current text content from the Android device clipboard."""
    return TermuxBridge.get_clipboard()

def write_clipboard(text: str) -> str:
    """Copy text content to the Android device clipboard.
    
    Args:
        text: The text to write to clipboard
    """
    return TermuxBridge.set_clipboard(text)

def get_wifi_status() -> str:
    """Get current Wi-Fi connection details including SSID, IP address, and link speed."""
    info = TermuxBridge.get_wifi_info()
    ssid = info.get("ssid", "Not connected")
    ip = info.get("ip", "N/A")
    speed = info.get("link_speed_mbps", "N/A")
    return f"Wi-Fi SSID: {ssid}, IP Address: {ip}, Link Speed: {speed} Mbps"

def speak_text(text: str) -> str:
    """Speak text aloud using the device Text-to-Speech (TTS) voice engine.
    
    Args:
        text: The message to speak
    """
    return TermuxBridge.speak(text)

def vibrate_device(duration_ms: int = 500) -> str:
    """Vibrate the phone hardware.
    
    Args:
        duration_ms: Vibration length in milliseconds (default 500ms)
    """
    return TermuxBridge.vibrate(duration_ms)

def analyze_camera_photo(prompt: str = "Describe what you see in this photo in detail.") -> str:
    """Take a photo using the phone's camera and analyze it with Gemini Vision AI.
    The temporary photo file is automatically destroyed immediately after analysis for privacy.
    
    Args:
        prompt: Question or instruction for analyzing the photo (e.g. "What objects are in front of me?")
    """
    photo_filename = f"temp_photo_{int(time.time())}.jpg"
    success = TermuxBridge.take_photo(camera_id=0, output_path=photo_filename)
    
    if not success or not os.path.exists(photo_filename):
        return "Failed to take photo. Please verify camera permissions for Termux:API."
    
    try:
        from config import GEMINI_API_KEY, DEFAULT_MODEL
        from google import genai
        from google.genai import types

        if not GEMINI_API_KEY:
            return "Camera photo taken, but GEMINI_API_KEY is not configured for vision analysis."

        client = genai.Client(api_key=GEMINI_API_KEY)
        with open(photo_filename, "rb") as f:
            image_bytes = f.read()

        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                prompt
            ]
        )
        return response.text or "Photo analyzed successfully."
    except Exception as e:
        return f"Error during camera photo vision analysis: {str(e)}"
    finally:
        # Security & Privacy: Immediately delete temporary photo file
        if os.path.exists(photo_filename):
            try:
                os.remove(photo_filename)
            except OSError:
                pass

def get_location_and_weather() -> str:
    """Get current GPS coordinates and fetch current real-time weather information using Open-Meteo API."""
    loc = TermuxBridge.get_location()
    lat = loc.get("latitude", 37.5665)
    lon = loc.get("longitude", 126.9780)
    
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("current_weather", {})
            temp = data.get("temperature", "N/A")
            wind = data.get("windspeed", "N/A")
            weather_code = data.get("weathercode", 0)
            return (
                f"Coordinates: Lat {lat:.4f}, Lon {lon:.4f} | "
                f"Temperature: {temp}°C, Wind Speed: {wind} km/h (Weather Code: {weather_code})"
            )
    except Exception as e:
        pass
    
    return f"Coordinates: Lat {lat}, Lon {lon} (Unable to reach weather server)"

def play_audio_file(file_path: str) -> str:
    """Play an audio/music file stored on the device.
    
    Args:
        file_path: Path to the audio file (e.g. /sdcard/Download/song.mp3)
    """
    if not os.path.exists(file_path) and TermuxBridge.is_termux_available():
        return f"File non-existent or inaccessible: {file_path}"
    return TermuxBridge.play_media(file_path)

def set_timer_alarm(seconds: int, label: str = "Timer Alert") -> str:
    """Set a timer countdown alarm. When the timer expires, it will vibrate and send a notification.
    
    Args:
        seconds: Duration in seconds to wait
        label: Description label for the timer
    """
    def timer_thread():
        time.sleep(seconds)
        TermuxBridge.vibrate(1000)
        TermuxBridge.send_notification("⏰ J.A.R.V.I.S. Timer Expired", f"{label} - {seconds} seconds completed!")
        TermuxBridge.speak(f"Sir, your timer for {label} has finished.")

    t = threading.Thread(target=timer_thread, daemon=True)
    t.start()
    return f"Timer set for {seconds} seconds ({label})."

def search_web_info(query: str) -> str:
    """Search for real-time information or answers on the web using privacy-focused DuckDuckGo API.
    
    Args:
        query: Search topic or question
    """
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_redirect=1&no_html=1"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            abstract = data.get("AbstractText", "")
            heading = data.get("Heading", "")
            related = data.get("RelatedTopics", [])
            
            summary = []
            if heading and abstract:
                summary.append(f"[{heading}]: {abstract}")
            
            for item in related[:3]:
                if isinstance(item, dict) and "Text" in item:
                    summary.append(f"- {item['Text']}")
            
            if summary:
                return "\n".join(summary)
            
            return f"No instant answer found on DuckDuckGo for query: '{query}'. Try refining the search term."
    except Exception as e:
        return f"Search error: {str(e)}"
    
    return f"Search query '{query}' completed with no results."

# Export list of available tool functions for Gemini LLM
JARVIS_TOOLS = [
    get_battery_status,
    set_flashlight,
    send_notification,
    show_toast_message,
    read_clipboard,
    write_clipboard,
    get_wifi_status,
    speak_text,
    vibrate_device,
    analyze_camera_photo,
    get_location_and_weather,
    play_audio_file,
    set_timer_alarm,
    search_web_info,
]
