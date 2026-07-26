"""SQLite database initialization for AIMS."""

import sqlite3
from pathlib import Path

DB_PATH = Path("storage/aims.db")


SYNC_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    summary_json TEXT,
    error_message TEXT
)
"""


RAW_SOURCE_SNAPSHOT_TABLE = """
CREATE TABLE IF NOT EXISTS raw_source_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    sync_run_id INTEGER,
    source_name TEXT NOT NULL,
    payload_json TEXT,
    success INTEGER DEFAULT 1,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


INDEX_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS index_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    index_name TEXT NOT NULL,
    close REAL,
    change_percent REAL,
    open REAL,
    high REAL,
    low REAL,
    amount REAL,
    volume REAL,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, index_name)
)
"""


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


LIMIT_UP_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS limit_up_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    industry TEXT,
    reason TEXT,
    change_percent REAL,
    amount REAL,
    free_float_market_cap REAL,
    total_market_cap REAL,
    turnover_rate REAL,
    seal_amount REAL,
    chain_days INTEGER,
    detail TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, stock_code)
)
"""


STOCK_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS stock_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    industry TEXT,
    role TEXT,
    change_percent REAL,
    amount REAL,
    free_float_market_cap REAL,
    total_market_cap REAL,
    turnover_rate REAL,
    seal_amount REAL,
    main_net_inflow REAL,
    is_limit_up INTEGER DEFAULT 0,
    chain_days INTEGER,
    detail TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, stock_code)
)
"""


STOCK_SNAPSHOT_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS stock_snapshot_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    close REAL,
    change_percent REAL,
    amount REAL,
    free_float_market_cap REAL,
    total_market_cap REAL,
    turnover_rate REAL,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, stock_code)
)
"""


CONCEPT_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS concept_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    concept_name TEXT NOT NULL,
    change_percent REAL,
    amount REAL,
    main_net_inflow REAL,
    leader_code TEXT,
    leader_name TEXT,
    leader_change_percent REAL,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, concept_name)
)
"""


PLAN_THEME_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS plan_theme_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    theme_id TEXT NOT NULL,
    theme_name TEXT NOT NULL,
    axis TEXT,
    score INTEGER DEFAULT 0,
    status TEXT,
    change_percent REAL,
    amount REAL,
    main_net_inflow REAL,
    limit_up_count INTEGER DEFAULT 0,
    leader_count INTEGER DEFAULT 0,
    catalyst_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, theme_id)
)
"""


PLAN_THEME_STOCK_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS plan_theme_stock_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    theme_id TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    role TEXT,
    change_percent REAL,
    main_net_inflow REAL,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, theme_id, stock_code)
)
"""


NEWS_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS news_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    event_time TEXT,
    url TEXT,
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

    cursor.execute(SYNC_RUNS_TABLE)
    cursor.execute(RAW_SOURCE_SNAPSHOT_TABLE)
    cursor.execute(INDEX_DAILY_TABLE)
    cursor.execute(MARKET_SENTIMENT_TABLE)
    cursor.execute(MARGIN_TABLE)
    cursor.execute(SECTOR_TABLE)
    cursor.execute(LIMIT_UP_DAILY_TABLE)
    cursor.execute(STOCK_DAILY_TABLE)
    cursor.execute(STOCK_SNAPSHOT_DAILY_TABLE)
    cursor.execute(CONCEPT_DAILY_TABLE)
    cursor.execute(PLAN_THEME_DAILY_TABLE)
    cursor.execute(PLAN_THEME_STOCK_DAILY_TABLE)
    cursor.execute(NEWS_DAILY_TABLE)
    _ensure_column(cursor, "sector_daily", "limit_up_count", "INTEGER")
    _ensure_column(cursor, "sector_daily", "amount", "REAL")
    _ensure_column(cursor, "sector_daily", "source", "TEXT")
    _ensure_column(cursor, "stock_daily", "amount", "REAL")
    _ensure_column(cursor, "stock_daily", "free_float_market_cap", "REAL")
    _ensure_column(cursor, "stock_daily", "total_market_cap", "REAL")
    _ensure_column(cursor, "stock_daily", "turnover_rate", "REAL")
    _ensure_column(cursor, "stock_daily", "seal_amount", "REAL")
    _ensure_column(cursor, "stock_daily", "main_net_inflow", "REAL")
    _ensure_column(cursor, "limit_up_daily", "free_float_market_cap", "REAL")
    _ensure_column(cursor, "limit_up_daily", "total_market_cap", "REAL")
    _ensure_column(cursor, "limit_up_daily", "turnover_rate", "REAL")
    _ensure_column(cursor, "limit_up_daily", "seal_amount", "REAL")

    conn.commit()
    conn.close()
