"""A-share trading calendar helpers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import akshare as ak


CACHE_PATH = Path("storage/trade_calendar.json")
CACHE_TTL = timedelta(days=7)


def _read_cache() -> dict | None:
    if not CACHE_PATH.exists():
        return None

    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _cache_is_fresh(payload: dict) -> bool:
    fetched_at = payload.get("fetched_at")
    if not fetched_at:
        return False

    try:
        timestamp = datetime.fromisoformat(fetched_at)
    except ValueError:
        return False

    return datetime.now() - timestamp < CACHE_TTL


def _write_cache(dates: list[str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(
            {
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                "dates": dates,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _fetch_calendar() -> list[str]:
    frame = ak.tool_trade_date_hist_sina()
    return sorted(frame["trade_date"].astype(str).tolist())


def get_trade_dates() -> set[str]:
    cached = _read_cache()
    if cached and _cache_is_fresh(cached):
        return set(cached.get("dates") or [])

    try:
        dates = _fetch_calendar()
    except Exception:  # noqa: BLE001 - stale cache is still useful.
        if cached:
            return set(cached.get("dates") or [])
        raise

    _write_cache(dates)
    return set(dates)


def is_trade_day(trade_date: str) -> bool:
    try:
        return trade_date in get_trade_dates()
    except Exception:  # noqa: BLE001 - last-resort fallback.
        return datetime.fromisoformat(trade_date).weekday() < 5
