"""Run local AKShare market collection and persist the result."""

import argparse
import json
from datetime import datetime

from backend.data_sources.akshare_provider import AkShareMarketDataProvider
from backend.services.trade_calendar import is_trade_day
from backend.storage.database import init_database
from backend.storage.markdown import generate_markdown
from backend.storage.repository import save_market_report


def collect_market_data(trade_date: str) -> dict:
    init_database()
    if not is_trade_day(trade_date):
        return {
            "schema_version": "1.0",
            "date": trade_date,
            "skipped": True,
            "reason": "non_trading_day",
            "message": f"{trade_date} 非 A 股交易日，无需同步",
            "sources": ["akshare.tool_trade_date_hist_sina"],
            "source_errors": [],
        }

    provider = AkShareMarketDataProvider()
    data = provider.collect(trade_date)
    markdown = generate_markdown(data)
    save_market_report(data, markdown)
    return data


def build_summary(data: dict) -> dict:
    if data.get("skipped"):
        return {
            "date": data.get("date"),
            "ok": False,
            "skipped": True,
            "reason": data.get("reason"),
            "message": data.get("message"),
            "source_errors": data.get("source_errors") or [],
        }

    margin_balance = data.get("margin_balance") or []
    sectors = data.get("sectors") or []
    indices = data.get("indices") or []
    news = data.get("news") or []
    stats = data.get("market_statistics") or {}

    def compact_errors(errors: list[dict]) -> list[dict]:
        compacted = []
        for row in errors:
            source = row.get("source")
            error = str(row.get("error") or "")
            non_blocking = (
                (source == "akshare.stock_zh_a_spot_em" and stats.get("up_count") is not None)
                or (source == "akshare.stock_board_industry_name_em" and len(sectors) > 0)
                or (source == "akshare.stock_info_global_*" and len(news) > 0)
            )
            compacted.append(
                {
                    "source": source,
                    "non_blocking": non_blocking,
                    "error": error if len(error) <= 220 else f"{error[:220]}...",
                }
            )
        return compacted

    return {
        "date": data.get("date"),
        "turnover": data.get("turnover"),
        "indices_count": len(indices),
        "indices": [
            {
                "name": row.get("name") or row.get("index_name"),
                "close": row.get("close"),
                "change_pct": row.get("change_pct"),
                "source": row.get("source"),
            }
            for row in indices
        ],
        "market_statistics": {
            "up_count": stats.get("up_count"),
            "down_count": stats.get("down_count"),
            "flat_count": stats.get("flat_count"),
            "limit_up_count": stats.get("limit_up_count"),
            "limit_down_count": stats.get("limit_down_count"),
        },
        "limit_chain_count": len(data.get("limit_chain_stocks") or []),
        "sector_count": len(sectors),
        "sector_top5": [
            {
                "name": row.get("sector_name") or row.get("name"),
                "limit_up_count": row.get("limit_up_count"),
                "change_percent": row.get("change_percent"),
                "amount": row.get("amount"),
            }
            for row in sectors[:5]
        ],
        "margin_balance_count": len(margin_balance),
        "margin_balance_range": {
            "start": margin_balance[0].get("date") if margin_balance else None,
            "end": margin_balance[-1].get("date") if margin_balance else None,
        },
        "news_count": len(news),
        "news_top3": [
            {
                "time": row.get("time") or row.get("date"),
                "category": row.get("category"),
                "title": row.get("title") or row.get("headline"),
                "source": row.get("source"),
            }
            for row in news[:3]
        ],
        "source_errors": compact_errors(data.get("source_errors") or []),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "date",
        nargs="?",
        default=datetime.now().date().isoformat(),
        help="Trade date formatted as YYYY-MM-DD.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Print the full collected JSON instead of a compact summary.",
    )
    args = parser.parse_args()

    result = collect_market_data(args.date)
    output = result if args.full else build_summary(result)
    print(json.dumps(output, ensure_ascii=False, indent=2))
