import os
import json
import requests
from typing import Dict, Any, Callable
from config import GEMINI_API_KEY, DEFAULT_MODEL, JARVIS_SYSTEM_PROMPT
from core import tools

class JarvisLLM:
    """Ultra-lightweight Gemini LLM Manager with multi-endpoint resolution."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("JARVIS_MODEL", "gemini-1.5-flash")
        self.working_url = None
        self.history = []

    def is_configured(self) -> bool:
        return bool(self.api_key or os.getenv("GEMINI_API_KEY"))

    def send_message(self, user_text: str) -> str:
        """Send message to Gemini REST API and handle responses."""
        api_key = (self.api_key or os.getenv("GEMINI_API_KEY", "")).strip().strip("'").strip('"')
        if not api_key:
            return (
                "Sir, GEMINI_API_KEY is missing.\n"
                "Please set your key in .env or run: export GEMINI_API_KEY='your_key'"
            )

        # Maintain session conversation history
        self.history.append({"role": "user", "parts": [{"text": user_text}]})

        # Keep history compact for fast mobile response
        if len(self.history) > 10:
            self.history = self.history[-10:]

        payload = {
            "systemInstruction": {"parts": [{"text": JARVIS_SYSTEM_PROMPT}]},
            "contents": self.history
        }
        headers = {"Content-Type": "application/json"}

        # If we already found a working URL for this session, use it directly
        if self.working_url:
            urls_to_try = [self.working_url]
        else:
            urls_to_try = [
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}",
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}",
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}",
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}",
            ]

        last_error = ""

        for target_url in urls_to_try:
            try:
                resp = requests.post(target_url, headers=headers, json=payload, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        reply_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        self.history.append({"role": "model", "parts": [{"text": reply_text}]})
                        self.working_url = target_url  # Save working endpoint
                        return reply_text
                    except (KeyError, IndexError):
                        return "Standing by, Sir."
                else:
                    last_error = f"Gemini API Notice [{resp.status_code}]: {resp.text}"
                    if resp.status_code == 404:
                        continue  # Try next endpoint
            except Exception as e:
                last_error = f"Connection error: {str(e)}"

        return last_error or "Apologies, Sir. Connection issue encountered."
