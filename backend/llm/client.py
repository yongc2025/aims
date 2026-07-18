"""LLM provider abstraction for AIMS.

Business modules should call LLMClient instead of depending on a specific provider.
"""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def chat(self, prompt: str) -> str:
        """Send prompt and return model response."""
        raise NotImplementedError
