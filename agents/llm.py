"""Free LLM wrapper.

Uses the OpenAI Python SDK pointed at any OpenAI-compatible FREE endpoint:
  * Groq (default)  -> https://api.groq.com/openai/v1   (free API key, no card)
  * Google Gemini   -> https://generativelanguage.googleapis.com/v1beta/openai/
  * Ollama (local)  -> http://localhost:11434/v1        (runs on your laptop)

If no key is configured the app still works: every agent has a rule-based
fallback, so the LLM only *adds* richer extraction and advice.
"""
import json
import os
import re

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-20b"


def _get_setting(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:  # Streamlit Cloud secrets
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


class LLM:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or _get_setting("LLM_API_KEY")
        self.base_url = base_url or _get_setting("LLM_BASE_URL", DEFAULT_BASE_URL)
        self.model = model or _get_setting("LLM_MODEL", DEFAULT_MODEL)
        self._client = None
        # Ollama does not need a real key
        if not self.api_key and "localhost" in self.base_url:
            self.api_key = "ollama"

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _client_obj(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def chat(self, system: str, user: str, temperature: float = 0.2) -> str:
        resp = self._client_obj().chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content or ""

    def chat_json(self, system: str, user: str) -> dict:
        """Ask for JSON and parse it robustly. Returns {} on any failure."""
        try:
            text = self.chat(system + "\nRespond with ONLY valid JSON, no markdown.", user)
            return parse_json(text)
        except Exception:
            return {}


def parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {}
