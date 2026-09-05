import os
import json
import requests
from typing import Dict, Any, Callable
from config import GEMINI_API_KEY, DEFAULT_MODEL, JARVIS_SYSTEM_PROMPT
from core import tools

class JarvisLLM:
    """Ultra-lightweight Gemini LLM Manager using direct REST API with automatic model fallbacks."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name or os.getenv("JARVIS_MODEL", "gemini-2.5-flash")
        self.history = []

    def is_configured(self) -> bool:
        return bool(self.api_key or os.getenv("GEMINI_API_KEY"))

    def send_message(self, user_text: str) -> str:
        """Send message to Gemini REST API and handle responses."""
        api_key = self.api_key or os.getenv("GEMINI_API_KEY", "")
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
            "system_instruction": {"parts": [{"text": JARVIS_SYSTEM_PROMPT}]},
            "contents": self.history
        }

        # Candidate models list for seamless fallback
        candidate_models = [self.model_name, "gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]
        headers = {"Content-Type": "application/json"}

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
                elif resp.status_code == 404:
                    continue  # Try fallback model
                else:
                    return f"Gemini API Notice ({resp.status_code}): {resp.text}"
            except Exception as e:
                return f"Apologies, Sir. Connection issue: {str(e)}"

        return "Apologies, Sir. Unable to connect to Gemini model API."
