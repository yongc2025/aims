"""OpenCode compatible LLM provider.

Configuration will be loaded from environment variables.
"""

import os

from .client import LLMClient


class OpenCodeClient(LLMClient):
    def __init__(self):
        self.base_url = os.getenv("OPENCODE_BASE_URL", "")
        self.api_key = os.getenv("OPENCODE_API_KEY", "")
        self.model = os.getenv("OPENCODE_MODEL", "")

    def chat(self, prompt: str) -> str:
        """Call OpenCode API.

        TODO:
        Implement OpenAI-compatible HTTP request after API endpoint is configured.
        """
        raise NotImplementedError("OpenCode API integration pending configuration")
