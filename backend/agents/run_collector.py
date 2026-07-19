"""AIMS collector pipeline entrypoint."""

import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from backend.agents.market_collector import MarketCollectorAgent
from backend.llm.provider import get_llm_client
from backend.storage.markdown import generate_markdown
from backend.storage.repository import save_market_report


def collect_market_data(trade_date: str):
    """Collect, validate, render, and persist one daily market report."""
    load_dotenv()

    prompt_template = Path("prompts/stock_collector_v1.md").read_text(
        encoding="utf-8"
    )
    agent = MarketCollectorAgent(get_llm_client(), prompt_template)
    data = agent.collect(datetime.fromisoformat(trade_date).date())
    markdown = generate_markdown(data)
    save_market_report(data, markdown)
    return data


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else datetime.now().date().isoformat()
    result = collect_market_data(date_arg)
    print(json.dumps(result, ensure_ascii=False, indent=2))
