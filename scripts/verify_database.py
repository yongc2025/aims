"""AIMS database verification script."""

from pathlib import Path
import sqlite3


DB_PATH = Path("storage/aims.db")


def verify_database():
    checks = []

    checks.append(("database_file", DB_PATH.exists()))

    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        required = {
            "market_reports",
            "market_sentiment_daily",
            "margin_balance_weekly",
            "sector_daily",
        }

        checks.append(("required_tables", required.issubset(tables)))
        conn.close()
    else:
        checks.append(("required_tables", False))

    return checks


if __name__ == "__main__":
    print("AIMS Database Verification")
    print("=" * 30)

    failed = False

    for name, status in verify_database():
        symbol = "✓" if status else "✗"
        print(f"{symbol} {name}")
        if not status:
            failed = True

    raise SystemExit(1 if failed else 0)
