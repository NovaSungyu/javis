import os
import json
import requests
from typing import Dict, Any, Callable
from config import GEMINI_API_KEY, DEFAULT_MODEL, JARVIS_SYSTEM_PROMPT
from core import tools

class JarvisLLM:
    """Ultra-lightweight Gemini LLM Manager using direct REST API."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("JARVIS_MODEL", "gemini-1.5-flash")
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

        # Preferred models
        candidate_models = ["gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro"]
        headers = {"Content-Type": "application/json"}

        last_error = ""

        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        reply_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        self.history.append({"role": "model", "parts": [{"text": reply_text}]})
                        return reply_text
                    except (KeyError, IndexError):
                        return "Standing by, Sir."
                else:
                    last_error = f"Gemini API Error [{resp.status_code}]: {resp.text}"
                    # If invalid key, stop looping and return error directly
                    if "API_KEY_INVALID" in resp.text or resp.status_code == 400:
                        return f"API Key Issue ({resp.status_code}): Please verify your Gemini API key."
            except Exception as e:
                last_error = f"Connection error: {str(e)}"

        return last_error or "Apologies, Sir. Connection issue encountered."
