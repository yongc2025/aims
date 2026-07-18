"""OpenCode compatible LLM provider."""

import os

import requests

from .client import LLMClient


class OpenCodeClient(LLMClient):
    """OpenCode client using OpenAI-compatible API format."""

    def __init__(self):
        self.base_url = os.getenv("OPENCODE_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("OPENCODE_API_KEY", "")
        self.model = os.getenv("OPENCODE_MODEL", "")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "120"))

    def chat(self, prompt: str) -> str:
        if not self.base_url:
            raise RuntimeError("OPENCODE_BASE_URL is not configured")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]
