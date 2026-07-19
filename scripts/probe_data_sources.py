"""Probe free/low-cost market data sources for AIMS.

This script does not write to the database. It checks which candidate data
sources are reachable and what fields they return in the current environment.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Callable


def dataframe_summary(df: Any, limit: int = 2) -> dict[str, Any]:
    """Return a compact, JSON-serializable summary of a pandas DataFrame."""
    return {
        "rows": int(len(df)),
        "columns": [str(column) for column in list(df.columns)],
        "sample": json.loads(df.head(limit).to_json(orient="records", force_ascii=False)),
    }


def run_probe(name: str, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        result = fn()
        if hasattr(result, "columns") and hasattr(result, "head"):
            return {
                "name": name,
                "ok": True,
                "data": dataframe_summary(result),
            }

        return {
            "name": name,
            "ok": True,
            "data": result,
        }
    except Exception as exc:  # noqa: BLE001 - probe should keep running.
        return {
            "name": name,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def probe_akshare(date: str | None) -> list[dict[str, Any]]:
    import akshare as ak

    compact_date = date.replace("-", "") if date else None

    probes: list[tuple[str, Callable[[], Any]]] = [
        (
            "akshare.index.shanghai_daily",
            lambda: ak.stock_zh_index_daily_em(symbol="sh000001").tail(5),
        ),
        (
            "akshare.stock.a_spot",
            lambda: ak.stock_zh_a_spot_em().head(20),
        ),
        (
            "akshare.board.industry",
            lambda: ak.stock_board_industry_name_em().head(20),
        ),
        (
            "akshare.margin.shanghai_macro",
            lambda: ak.macro_china_market_margin_sh().tail(10),
        ),
        (
            "akshare.margin.shenzhen_macro",
            lambda: ak.macro_china_market_margin_sz().tail(10),
        ),
    ]

    if compact_date:
        probes.extend(
            [
                (
                    "akshare.limit_up.pool",
                    lambda: ak.stock_zt_pool_em(date=compact_date).head(20),
                ),
                (
                    "akshare.limit_down.pool",
                    lambda: ak.stock_zt_pool_dtgc_em(date=compact_date).head(20),
                ),
            ]
        )

    return [run_probe(name, fn) for name, fn in probes]


def probe_baostock(date: str | None) -> list[dict[str, Any]]:
    import baostock as bs

    target_date = date or "2024-07-17"
    fields = "date,code,open,high,low,close,volume,amount,pctChg"

    def query_shanghai_index():
        login = bs.login()
        if login.error_code != "0":
            raise RuntimeError(login.error_msg)

        try:
            result = bs.query_history_k_data_plus(
                "sh.000001",
                fields,
                start_date=target_date,
                end_date=target_date,
                frequency="d",
            )
            if result.error_code != "0":
                raise RuntimeError(result.error_msg)

            rows = []
            while result.next():
                rows.append(result.get_row_data())

            return {
                "rows": len(rows),
                "columns": fields.split(","),
                "sample": [dict(zip(fields.split(","), row)) for row in rows[:2]],
            }
        finally:
            bs.logout()

    return [run_probe("baostock.index.shanghai_daily", query_shanghai_index)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date",
        help="Optional trade date for date-specific probes, formatted as YYYY-MM-DD.",
    )
    args = parser.parse_args()

    report = {
        "date": args.date,
        "sources": [
            *probe_akshare(args.date),
            *probe_baostock(args.date),
        ],
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
