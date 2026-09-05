import os
import json
import requests
from typing import Dict, Any, Callable
from config import GEMINI_API_KEY, DEFAULT_MODEL, JARVIS_SYSTEM_PROMPT
from core import tools

class JarvisLLM:
    """Ultra-lightweight Gemini LLM Manager with detailed API key diagnostics."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("JARVIS_MODEL", "gemini-1.5-flash")
        self.history = []

    def is_configured(self) -> bool:
        return bool(self.api_key or os.getenv("GEMINI_API_KEY"))

    def send_message(self, user_text: str) -> str:
        """Send message to Gemini REST API and handle responses."""
        raw_key = self.api_key or os.getenv("GEMINI_API_KEY", "")
        # Clean API key strictly
        api_key = "".join(c for c in raw_key if c.isalnum() or c in "_-").strip()

        if not api_key:
            return (
                "Sir, GEMINI_API_KEY is missing.\n"
                "Please set your key in .env or run: export GEMINI_API_KEY='your_key'"
            )

        # Masked key representation for user debugging
        masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key

        # Prepend JARVIS system directives to first user prompt if history is empty
        if not self.history:
            combined_prompt = f"[System Protocol]: {JARVIS_SYSTEM_PROMPT}\n\n[User Request]: {user_text}"
            self.history.append({"role": "user", "parts": [{"text": combined_prompt}]})
        else:
            self.history.append({"role": "user", "parts": [{"text": user_text}]})

        # Keep history compact for fast mobile response
        if len(self.history) > 10:
            self.history = self.history[-10:]

        payload = {"contents": self.history}
        headers = {"Content-Type": "application/json"}

        # Tried endpoints
        candidate_urls = [
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}",
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}",
        ]

        last_error = ""

        for url in candidate_urls:
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
                    last_error = f"API Response ({resp.status_code}) using key [{masked_key}]: {resp.text}"
            except Exception as e:
                last_error = f"Connection error: {str(e)}"

        return last_error or "Apologies, Sir. Connection issue encountered."
