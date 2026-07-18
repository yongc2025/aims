"""Repository functions for market data persistence."""

import json
from .database import get_connection


def save_market_report(data: dict, markdown: str = ""):
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
