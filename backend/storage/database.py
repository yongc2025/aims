"""SQLite database initialization for AIMS."""

import sqlite3
from pathlib import Path

DB_PATH = Path("storage/aims.db")


MARKET_SENTIMENT_TABLE = """
CREATE TABLE IF NOT EXISTS market_sentiment_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT UNIQUE NOT NULL,
    up_count INTEGER,
    down_count INTEGER,
    limit_up_count INTEGER,
    limit_down_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


MARGIN_TABLE = """
CREATE TABLE IF NOT EXISTS margin_balance_weekly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_date TEXT UNIQUE NOT NULL,
    margin_balance REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


SECTOR_TABLE = """
CREATE TABLE IF NOT EXISTS sector_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    sector_name TEXT NOT NULL,
    change_percent REAL,
    limit_up_count INTEGER,
    amount REAL,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _ensure_column(cursor, table_name: str, column_name: str, definition: str):
    columns = {row[1] for row in cursor.execute(f"PRAGMA table_info({table_name})")}
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS market_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT UNIQUE NOT NULL,
            schema_version TEXT NOT NULL,
            json_content TEXT NOT NULL,
            markdown_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(MARKET_SENTIMENT_TABLE)
    cursor.execute(MARGIN_TABLE)
    cursor.execute(SECTOR_TABLE)
    _ensure_column(cursor, "sector_daily", "limit_up_count", "INTEGER")
    _ensure_column(cursor, "sector_daily", "amount", "REAL")
    _ensure_column(cursor, "sector_daily", "source", "TEXT")

    conn.commit()
    conn.close()
