"""Run local AKShare market collection and persist the result."""

import argparse
import json
import logging
import os
from datetime import datetime

from backend.data_sources.akshare_provider import AkShareMarketDataProvider
from backend.services.trade_calendar import is_trade_day
from backend.storage.database import init_database
from backend.storage.markdown import generate_markdown
from backend.storage.repository import finish_sync_run, save_market_report, start_sync_run

logger = logging.getLogger(__name__)


def collect_market_data(trade_date: str, *, preserve_realtime_snapshot: bool = False) -> dict:
    # Only configure logging if the root logger has no handlers yet (e.g. CLI mode).
    # When running via the API, main.py already sets up the FileHandler with UTF-8.
    if not logging.getLogger().hasHandlers():
        log_file = os.environ.get("AIMS_LOG_FILE")
        if log_file:
            handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
            handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
            ))
            logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
                force=True,
            )
    logger.info("[数据采集器] %s | === 开始数据采集 ===", trade_date)
    init_database()
    logger.info("[数据采集器] %s | init_database | ✅ 数据库已初始化", trade_date)
    sync_run_id = start_sync_run(trade_date)
    logger.info("[数据采集器] %s | start_sync_run | ✅ 同步任务ID=%s", trade_date, sync_run_id)

    if not is_trade_day(trade_date):
        logger.info("[数据采集器] %s | is_trade_day | ⏭️ 非交易日，跳过", trade_date)
        data = {
            "schema_version": "1.0",
            "date": trade_date,
            "skipped": True,
            "reason": "non_trading_day",
            "message": f"{trade_date} 非 A 股交易日，无需同步",
            "sources": ["akshare.tool_trade_date_hist_sina"],
            "source_errors": [],
        }
        finish_sync_run(sync_run_id, "skipped", build_summary(data))
        data["sync_run_id"] = sync_run_id
        return data

    try:
        logger.info("[数据采集器] %s | AkShareMarketDataProvider.collect | 🚀 开始调用...", trade_date)
        provider = AkShareMarketDataProvider()
        data = provider.collect(trade_date)
        logger.info("[数据采集器] %s | AkShareMarketDataProvider.collect | ✅ 数据采集完成", trade_date)

        logger.info("[数据采集器] %s | generate_markdown | 📝 生成Markdown报告...", trade_date)
        markdown = generate_markdown(data)

        logger.info("[数据采集器] %s | save_market_report | 💾 保存到数据库...", trade_date)
        data = save_market_report(
            data,
            markdown,
            sync_run_id=sync_run_id,
            preserve_realtime_snapshot=preserve_realtime_snapshot,
        )
        data["sync_run_id"] = sync_run_id
        logger.info("[数据采集器] %s | save_market_report | ✅ 数据库保存完成", trade_date)

        summary = build_summary(data)
        logger.info("[数据采集器] %s | finish_sync_run | ✅ 同步成功", trade_date)
        finish_sync_run(sync_run_id, "success", summary)
        logger.info("[数据采集器] %s | === 同步流程完全结束 === | 🎉", trade_date)
        return data
    except Exception as exc:
        logger.error("[数据采集器] %s | collect_market_data | ❌ 同步失败: %s", trade_date, exc, exc_info=True)
        finish_sync_run(
            sync_run_id,
            "failed",
            {"date": trade_date},
            f"{type(exc).__name__}: {exc}",
        )
        raise


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
    stock_snapshot = data.get("stock_snapshot") or []
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
        "stock_snapshot_count": len(stock_snapshot),
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

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
    print()
    print("=" * 60)
    print(json.dumps(output, ensure_ascii=False, indent=2))
