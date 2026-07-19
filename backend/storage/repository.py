"""Repository functions for market data persistence."""

import json
from .database import get_connection


def _number_or_none(value):
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_list(value):
    return value if isinstance(value, list) else []


def _merge_with_existing_report(data: dict) -> dict:
    trade_date = data.get("date")
    if not trade_date:
        return data

    existing = get_market_report(trade_date)
    if not existing:
        return data

    previous = existing.get("data") or {}
    if not isinstance(previous, dict):
        return data

    merged = dict(data)
    for key in ("limit_chain_stocks", "sectors", "sector_data", "sector_daily", "news"):
        if not _as_list(merged.get(key)) and _as_list(previous.get(key)):
            merged[key] = previous.get(key)

    previous_stats = previous.get("market_statistics") or {}
    current_stats = merged.get("market_statistics") or {}
    if isinstance(previous_stats, dict) and isinstance(current_stats, dict):
        stats = dict(current_stats)
        for key in ("limit_up_count", "limit_down_count", "up_count", "down_count", "flat_count"):
            if _number_or_none(stats.get(key)) in (None, 0) and _number_or_none(previous_stats.get(key)) not in (None, 0):
                stats[key] = previous_stats.get(key)
        merged["market_statistics"] = stats

    return merged


def save_market_report(data: dict, markdown: str = ""):
    data = _merge_with_existing_report(data)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO market_reports
        (trade_date, schema_version, json_content, markdown_content)
        VALUES (?, ?, ?, ?)
        """,
        (
            data.get("date"),
            data.get("schema_version", "1.0"),
            json.dumps(data, ensure_ascii=False),
            markdown,
        ),
    )

    market_statistics = data.get("market_statistics") or {}
    if isinstance(market_statistics, dict):
        cursor.execute(
            """
            INSERT OR REPLACE INTO market_sentiment_daily
            (trade_date, up_count, down_count, limit_up_count, limit_down_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.get("date"),
                _number_or_none(market_statistics.get("up_count")),
                _number_or_none(market_statistics.get("down_count")),
                _number_or_none(market_statistics.get("limit_up_count")),
                _number_or_none(market_statistics.get("limit_down_count")),
            ),
        )

    sectors = _as_list(
        data.get("sectors") or data.get("sector_data") or data.get("sector_daily")
    )
    if sectors:
        cursor.execute("DELETE FROM sector_daily WHERE trade_date=?", (data.get("date"),))

    for sector in sectors:
        if not isinstance(sector, dict):
            continue

        sector_name = sector.get("sector_name") or sector.get("name")
        if not sector_name:
            continue

        cursor.execute(
            """
            INSERT INTO sector_daily
            (trade_date, sector_name, change_percent, limit_up_count, amount, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("date"),
                sector_name,
                _number_or_none(
                    sector.get("change_percent")
                    or sector.get("change")
                    or sector.get("value")
                ),
                _number_or_none(
                    sector.get("limit_up_count")
                    or sector.get("limitCount")
                    or sector.get("limit_count")
                ),
                _number_or_none(sector.get("amount") or sector.get("volume")),
                sector.get("source"),
            ),
        )

    margin_rows = _as_list(data.get("margin_balance"))
    for row in margin_rows:
        if not isinstance(row, dict):
            continue

        week_date = row.get("date") or row.get("week_date")
        margin_balance = row.get("margin_balance") or row.get("value")
        if not week_date:
            continue

        cursor.execute(
            """
            INSERT OR REPLACE INTO margin_balance_weekly
            (week_date, margin_balance)
            VALUES (?, ?)
            """,
            (
                week_date,
                _number_or_none(margin_balance),
            ),
        )

    conn.commit()
    conn.close()


def get_market_report(trade_date: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT json_content, markdown_content FROM market_reports WHERE trade_date=?",
        (trade_date,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "data": json.loads(row[0]),
        "markdown": row[1],
    }


def get_latest_market_report():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT trade_date, json_content, markdown_content
        FROM market_reports
        ORDER BY trade_date DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "date": row[0],
        "data": json.loads(row[1]),
        "markdown": row[2],
    }


def get_recent_market_reports(limit: int = 30):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT trade_date, json_content, markdown_content
        FROM market_reports
        ORDER BY trade_date DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "date": row[0],
            "data": json.loads(row[1]),
            "markdown": row[2],
        }
        for row in rows
    ]
