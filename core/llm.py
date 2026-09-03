import os
from typing import List, Dict, Any, Callable
from config import GEMINI_API_KEY, DEFAULT_MODEL, JARVIS_SYSTEM_PROMPT
from core import tools

class JarvisLLM:
    """LLM Manager for JARVIS using Google Gemini API."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self.client = None
        self.chat = None
        self._initialize_client()

    def _initialize_client(self):
        if not self.api_key:
            return
        
        try:
            from google import genai
            from google.genai import types

            self.client = genai.Client(api_key=self.api_key)
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=JARVIS_SYSTEM_PROMPT,
                    tools=tools.JARVIS_TOOLS,
                    temperature=0.7,
                ),
            )
        except Exception as e:
            print(f"[JARVIS Warning] Failed to initialize Gemini API client: {e}")
            self.client = None

    def is_configured(self) -> bool:
        return self.client is not None and self.chat is not None

    def send_message(self, user_text: str) -> str:
        """Send a text message to JARVIS and return the response."""
        if not self.is_configured():
            return (
                "Sir, GEMINI_API_KEY is not configured yet. "
                "Please add your API key to the .env file or export GEMINI_API_KEY in Termux.\n"
                "You can get a free API key at: https://aistudio.google.com/"
            )

        try:
            tool_map = {fn.__name__: fn for fn in tools.JARVIS_TOOLS}
            response = self.chat.send_message(user_text)
            
            # Handle manual tool execution if automatic handling returns function calls
            if hasattr(response, 'function_calls') and response.function_calls:
                tool_results = []
                for call in response.function_calls:
                    fn_name = call.name
                    args = call.args or {}
                    if fn_name in tool_map:
                        result = tool_map[fn_name](**args)
                        tool_results.append(f"Function {fn_name} result: {result}")
                
                # Send tool execution results back to model
                followup_text = "\n".join(tool_results)
                second_response = self.chat.send_message(
                    f"[System Tool Execution Result]: {followup_text}"
                )
                return second_response.text

            return response.text or "Standing by, Sir."
        except Exception as e:
            return f"Apologies, Sir. An error occurred while processing your request: {str(e)}"
