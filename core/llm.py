import os
import json
import requests
from typing import Dict, Any, Callable
from config import GEMINI_API_KEY, DEFAULT_MODEL, JARVIS_SYSTEM_PROMPT
from core import tools

class JarvisLLM:
    """Ultra-lightweight LLM Manager supporting Google Gemini API (AIza / AQ formats) & Groq."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
        self.model_name = os.getenv("JARVIS_MODEL", "gemini-1.5-flash")
        self.history = []

    def is_configured(self) -> bool:
        return bool(self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY"))

    def send_message(self, user_text: str) -> str:
        """Send message to Gemini REST API or Groq API."""
        raw_key = self.api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
        # Strip only enclosing whitespace/quotes, preserving all valid key characters (+, /, =, _, -, .)
        api_key = raw_key.strip().strip("'").strip('"')

        if not api_key:
            return (
                "Sir, API_KEY is missing.\n"
                "Please set your key in .env or run: export GEMINI_API_KEY='your_key'"
            )

        # Detect Groq API Key (starts with gsk_)
        if api_key.startswith("gsk_"):
            return self._send_groq_message(user_text, api_key)

        return self._send_gemini_message(user_text, api_key)

    def _send_groq_message(self, user_text: str, api_key: str) -> str:
        """Handle Groq AI API calls."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": JARVIS_SYSTEM_PROMPT}]
        for turn in self.history:
            messages.append(turn)
        messages.append({"role": "user", "content": user_text})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"]
                self.history.append({"role": "user", "content": user_text})
                self.history.append({"role": "assistant", "content": reply})
                return reply
            else:
                return f"Groq API Notice [{resp.status_code}]: {resp.text}"
        except Exception as e:
            return f"Groq Connection Error: {str(e)}"

    def _send_gemini_message(self, user_text: str, api_key: str) -> str:
        """Handle Google Gemini REST API calls supporting AIza and AQ authentication methods."""
        masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key

        if not self.history:
            combined_prompt = f"[System Protocol]: {JARVIS_SYSTEM_PROMPT}\n\n[User Request]: {user_text}"
            self.history.append({"role": "user", "parts": [{"text": combined_prompt}]})
        else:
            self.history.append({"role": "user", "parts": [{"text": user_text}]})

        if len(self.history) > 10:
            self.history = self.history[-10:]

        payload = {"contents": self.history}

        # Multi-strategy authentication:
        # 1. Official Google Header (x-goog-api-key) - Standard for modern Google Cloud & AI Studio
        # 2. Query param (?key=)
        # 3. Bearer Token (Authorization: Bearer) - Standard for AQ... OAuth/STS tokens
        auth_strategies = [
            {
                "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                "headers": {"Content-Type": "application/json", "x-goog-api-key": api_key}
            },
            {
                "url": f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                "headers": {"Content-Type": "application/json"}
            },
            {
                "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            },
            {
                "url": f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}",
                "headers": {"Content-Type": "application/json"}
            }
        ]

        last_error = ""

        for req in auth_strategies:
            try:
                resp = requests.post(req["url"], headers=req["headers"], json=payload, timeout=15)
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
