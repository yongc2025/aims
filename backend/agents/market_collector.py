"""A-share market data collector agent."""

from datetime import date

from .json_parser import extract_json
from .validator import MarketDataValidator


class MarketCollectorAgent:
    """Collect A-share market data through LLM."""

    def __init__(self, llm_client, prompt_template: str):
        self.llm = llm_client
        self.prompt_template = prompt_template
        self.validator = MarketDataValidator()

    def collect(self, trade_date: date) -> dict:
        """Run complete collection pipeline.

        Flow:
        date -> prompt -> LLM -> JSON extraction -> validation
        """
        prompt = self.prompt_template.replace(
            "{{date}}",
            trade_date.isoformat(),
        )

        response = self.llm.chat(prompt)
        payload = extract_json(response)

        return self.validator.validate(payload)
