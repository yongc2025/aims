"""AIMS collector pipeline entrypoint."""

import sys
from datetime import datetime

from backend.agents.market_collector import MarketCollectorAgent
from backend.agents.validator_agent import validate_market_data
from backend.storage.markdown import generate_markdown
from backend.storage.repository import save_market_report


def collect_market_data(trade_date: str):
    """Run the