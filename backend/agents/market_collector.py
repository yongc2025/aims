"""A-share market data collector agent."""

from datetime import date


class MarketCollectorAgent:
    def __init__(self, llm_client, prompt_template: str):
        self.llm = llm_client
        self.prompt_template = prompt_template

    def collect(self, trade_date: date) -> str:
        """Collect market data for a trading date.

        Current stage returns raw LLM output.
        Validation and persistence will be added next.
        """
        prompt = self.prompt_template.replace(
            "{{date}}",
            trade_date.isoformat(),
        )
        return self.llm.chat(prompt)
