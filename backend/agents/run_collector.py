"""AIMS collector pipeline entrypoint."""

from backend.agents.market_collector import MarketCollectorAgent


def collect_market_data(trade_date: str):
    agent = MarketCollectorAgent()
    return agent.collect(trade_date)


if __name__ == "__main__":
    result = collect_market_data("2026-07-17")
    print(result)
