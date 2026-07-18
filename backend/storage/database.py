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
    margin_balance