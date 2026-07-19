"""Repository layer for dashboard analysis data."""

from .database import get_connection


def get_margin_trend():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT week_date, margin_balance FROM margin_balance_weekly ORDER BY week_date"
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"date": row[0], "value": row[1]}
        for row in rows
    ]


def get_sentiment_trend():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT trade_date, up_count, down_count, limit_up_count, limit_down_count
        FROM market_sentiment_daily
        ORDER BY trade_date
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "date": row[0],
            "up": row[1],
            "down": row[2],
            "limit_up": row[3],
            "limit_down": row[4],
        }
        for row in rows
    ]


def get_sector_heatmap():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT trade_date, sector_name, change_percent, limit_up_count, amount, source
        FROM sector_daily
        ORDER BY trade_date DESC, limit_up_count DESC, change_percent DESC
        LIMIT 20
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "date": row[0],
            "name": row[1],
            "value": row[2],
            "change_percent": row[2],
            "limit_up_count": row[3],
            "amount": row[4],
            "source": row[5],
        }
        for row in rows
    ]
