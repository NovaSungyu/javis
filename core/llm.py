import os
import json
import requests
from typing import Dict, Any, Callable, Optional
from config import GEMINI_API_KEY, DEFAULT_MODEL, JARVIS_SYSTEM_PROMPT
from core import tools

class JarvisLLM:
    """Ultra-lightweight LLM Manager supporting Google Gemini API (AIza / AQ formats) & Groq."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
        # Keep config.py / JARVIS_MODEL support, but avoid the retired 1.5 default.
        self.model_name = model_name or os.getenv("JARVIS_MODEL", "gemini-2.5-flash")
        self.discovered_model: Optional[str] = None
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

    def _discover_model(self, api_key: str) -> Optional[str]:
        """Find a model available to this API key that supports generateContent."""
        headers = {"x-goog-api-key": api_key}

        for version in ("v1beta", "v1"):
            url = f"https://generativelanguage.googleapis.com/{version}/models"

            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    continue

                models = resp.json().get("models", [])

                preferred_names = [
                    self.model_name,
                    "gemini-3.7-flash",
                    "gemini-3.6-flash",
                    "gemini-3.5-flash",
                    "gemini-2.5-flash",
                    "gemini-2.5-flash-lite",
                ]

                for preferred_name in preferred_names:
                    for model in models:
                        name = model.get("name", "")
                        methods = model.get("supportedGenerationMethods", [])
                        if (
                            name.replace("models/", "") == preferred_name
                            and "generateContent" in methods
                        ):
                            clean_name = name.replace("models/", "")
                            print(f"[JARVIS] Model discovered: {clean_name}")
                            return f"{version}/{clean_name}"

                for model in models:
                    name = model.get("name", "")
                    methods = model.get("supportedGenerationMethods", [])
                    clean_name = name.replace("models/", "")

                    if (
                        "generateContent" in methods
                        and "flash" in clean_name.lower()
                    ):
                        print(f"[JARVIS] Model discovered: {clean_name}")
                        return f"{version}/{clean_name}"

                for model in models:
                    name = model.get("name", "")
                    methods = model.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        clean_name = name.replace("models/", "")
                        print(f"[JARVIS] Model discovered: {clean_name}")
                        return f"{version}/{clean_name}"

            except requests.RequestException as e:
                print(f"[JARVIS] Model discovery error: {e}")

        return None

    def _send_gemini_message(self, user_text: str, api_key: str) -> str:
        """Handle Google Gemini REST API calls using the AI Studio API-key header."""
        masked_key = (
            f"{api_key[:6]}...{api_key[-4:]}"
            if len(api_key) > 10
            else "***"
        )

        if not self.history:
            combined_prompt = (
                f"[System Protocol]: {JARVIS_SYSTEM_PROMPT}\n\n"
                f"[User Request]: {user_text}"
            )
            self.history.append({
                "role": "user",
                "parts": [{"text": combined_prompt}]
            })
        else:
            self.history.append({
                "role": "user",
                "parts": [{"text": user_text}]
            })

        if len(self.history) > 10:
            self.history = self.history[-10:]

        payload = {"contents": self.history}

        if not self.discovered_model:
            self.discovered_model = self._discover_model(api_key)

        if not self.discovered_model:
            return (
                f"Gemini model discovery failed using key [{masked_key}]. "
                "The API key may be invalid, restricted, or have no accessible "
                "generateContent models."
            )

        version, model_name = self.discovered_model.split("/", 1)
        endpoint = (
            f"https://generativelanguage.googleapis.com/"
            f"{version}/models/{model_name}:generateContent"
        )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }

        try:
            resp = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            if resp.status_code != 200:
                return (
                    f"API Response ({resp.status_code}) using key "
                    f"[{masked_key}]: {resp.text}"
                )

            data = resp.json()

            try:
                reply_text = (
                    data["candidates"][0]["content"]["parts"][0]["text"]
                )
            except (KeyError, IndexError, TypeError):
                return "Standing by, Sir."

            self.history.append({
                "role": "model",
                "parts": [{"text": reply_text}]
            })
            return reply_text

        except requests.RequestException as e:
            return f"Connection error: {str(e)}"
