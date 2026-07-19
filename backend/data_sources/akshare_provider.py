"""AKShare-backed market data provider for AIMS."""

from __future__ import annotations

import re
import os
import socket
from datetime import datetime
from multiprocessing import get_context
from typing import Any

import akshare as ak
import pandas as pd
import requests


socket.setdefaulttimeout(15)
_REQUEST_WITHOUT_DEFAULT_TIMEOUT = requests.sessions.Session.request


def _request_with_default_timeout(self, method, url, **kwargs):
    kwargs.setdefault("timeout", 15)
    return _REQUEST_WITHOUT_DEFAULT_TIMEOUT(self, method, url, **kwargs)


requests.sessions.Session.request = _request_with_default_timeout

OPTIONAL_SOURCE_TIMEOUT_SECONDS = 20
ENABLE_SLOW_SOURCES = os.getenv("AIMS_ENABLE_SLOW_SOURCES", "").lower() in {
    "1",
    "true",
    "yes",
}


def _date_compact(trade_date: str) -> str:
    return trade_date.replace("-", "")


def _number_or_none(value: Any) -> float | int | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text_or_none(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _first_value(row: pd.Series, *columns: str) -> Any:
    for column in columns:
        if column in row:
            value = row.get(column)
            if value is not None and not pd.isna(value):
                return value
    return None


def _date_from_value(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()

    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(timestamp).date().isoformat()

    text = str(value)
    try:
        return pd.to_datetime(text).date().isoformat()
    except (TypeError, ValueError):
        return text[:10]


def _load_limit_up_pool(trade_date: str) -> pd.DataFrame:
    return ak.stock_zt_pool_em(date=_date_compact(trade_date))


def _load_limit_down_pool(trade_date: str) -> pd.DataFrame:
    return ak.stock_zt_pool_dtgc_em(date=_date_compact(trade_date))


def _load_a_spot() -> pd.DataFrame:
    return ak.stock_zh_a_spot_em()


def _load_industry_board() -> pd.DataFrame:
    return ak.stock_board_industry_name_em()


def _worker(source_name: str, args: tuple[Any, ...], queue) -> None:
    functions = {
        "index_row": _index_row,
        "a_spot": _load_a_spot,
        "sina_a_spot_stats": _sina_a_spot_statistics,
        "industry_board": _load_industry_board,
        "news_rows": _news_rows,
    }
    try:
        queue.put({"ok": True, "value": functions[source_name](*args)})
    except Exception as exc:  # noqa: BLE001 - returned to parent as source error.
        queue.put({"ok": False, "error": f"{type(exc).__name__}: {exc}"})


def _run_optional_source(
    source: str,
    errors: list[dict[str, str]],
    source_name: str,
    args: tuple[Any, ...] = (),
    timeout: int = OPTIONAL_SOURCE_TIMEOUT_SECONDS,
) -> Any | None:
    context = get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_worker, args=(source_name, args, queue))
    process.start()
    process.join(timeout)

    if process.is_alive():
        process.kill()
        process.join()
        errors.append({"source": source, "error": f"TimeoutError: exceeded {timeout}s"})
        return None

    if queue.empty():
        if process.exitcode not in (0, None):
            errors.append({"source": source, "error": f"ProcessError: exit code {process.exitcode}"})
        return None

    result = queue.get()
    if result.get("ok"):
        return result.get("value")

    errors.append({"source": source, "error": result.get("error", "unknown error")})
    return None


def _safe_frame(source: str, errors: list[dict[str, str]], loader) -> pd.DataFrame:
    try:
        result = loader()
        if hasattr(result, "empty"):
            return result
    except Exception as exc:  # noqa: BLE001 - each source should fail independently.
        errors.append({"source": source, "error": f"{type(exc).__name__}: {exc}"})
    return pd.DataFrame()


def _safe_list(source: str, errors: list[dict[str, str]], loader) -> list[dict[str, Any]]:
    try:
        return loader()
    except Exception as exc:  # noqa: BLE001 - each source should fail independently.
        errors.append({"source": source, "error": f"{type(exc).__name__}: {exc}"})
    return []


def _limit_chain_stocks(limit_up_pool: pd.DataFrame) -> list[dict[str, Any]]:
    if limit_up_pool.empty:
        return []

    rows = []
    sorted_pool = limit_up_pool.sort_values(
        by="连板数",
        ascending=False,
        na_position="last",
    )

    for _, row in sorted_pool.head(50).iterrows():
        rows.append(
            {
                "stock_code": str(row.get("代码", "")),
                "stock_name": str(row.get("名称", "")),
                "chain_days": _number_or_none(row.get("连板数")),
                "detail": _text_or_none(row.get("涨停统计")),
                "industry": _text_or_none(row.get("所属行业")),
                "reason": _text_or_none(row.get("所属行业")),
            }
        )

    return rows


def _empty_market_daily(trade_date: str, errors: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "date": trade_date,
        "turnover": None,
        "total_turnover": None,
        "indices": [],
        "index_data": [],
        "shanghai_index": None,
        "market_statistics": {
            "up_count": None,
            "down_count": None,
            "flat_count": None,
            "limit_up_count": None,
            "limit_down_count": None,
        },
        "limit_chain_stocks": [],
        "sectors": [],
        "margin_balance": [],
        "news": [],
        "sources": [],
        "source_errors": [
            *errors,
            {
                "source": "akshare.stock_zt_pool_em",
                "error": "No trading-day limit-up data for requested date; skipped intraday snapshot.",
            },
        ],
    }


def _index_row(symbol: str, name: str, trade_date: str) -> dict[str, Any] | None:
    return _akshare_index_row(symbol, name, trade_date)


def _sina_index_rows(errors: list[dict[str, str]]) -> list[dict[str, Any]]:
    symbols = {
        "s_sh000001": "上证指数",
        "s_sz399001": "深证成指",
        "s_sz399006": "创业板指",
    }
    url = f"https://hq.sinajs.cn/list={','.join(symbols)}"

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://finance.sina.com.cn/",
            },
            timeout=8,
        )
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - fallback to AKShare below.
        errors.append({"source": "sina.hq.sinajs.cn:index", "error": f"{type(exc).__name__}: {exc}"})
        return []

    text = response.content.decode("gbk", errors="ignore")
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if '="' not in line:
            continue
        key = line.split('="', 1)[0].replace("var hq_str_", "")
        name = symbols.get(key)
        if not name:
            continue

        values = line.split('="', 1)[1].rstrip('";').split(",")
        if len(values) < 4:
            continue

        amount = _number_or_none(values[5]) if len(values) > 5 else None
        rows.append(
            {
                "name": name,
                "index_name": name,
                "close": _number_or_none(values[1]),
                "change_pct": _number_or_none(values[3]),
                "high": None,
                "low": None,
                "open": None,
                "amount": amount * 10_000 if isinstance(amount, (int, float)) else None,
                "volume": _number_or_none(values[4]) if len(values) > 4 else None,
                "source": f"sina.hq.sinajs.cn:{key}",
            }
        )

    return rows


def _akshare_index_row(symbol: str, name: str, trade_date: str) -> dict[str, Any] | None:
    frame = ak.stock_zh_index_daily_em(symbol=symbol)
    if frame.empty:
        return None

    rows = frame.copy()
    date_column = "date" if "date" in rows.columns else "日期"
    rows["__date"] = rows[date_column].map(_date_from_value)
    rows = rows.dropna(subset=["__date"]).sort_values("__date")
    rows = rows[rows["__date"] <= trade_date]
    if rows.empty:
        return None

    latest = rows.iloc[-1]
    previous = rows.iloc[-2] if len(rows) >= 2 else None
    close = _number_or_none(_first_value(latest, "close", "收盘"))
    previous_close = (
        _number_or_none(_first_value(previous, "close", "收盘"))
        if previous is not None
        else None
    )
    change_pct = None
    if close is not None and previous_close not in (None, 0):
        change_pct = (close - previous_close) / previous_close * 100

    return {
        "name": name,
        "index_name": name,
        "close": close,
        "change_pct": change_pct,
        "high": _number_or_none(_first_value(latest, "high", "最高")),
        "low": _number_or_none(_first_value(latest, "low", "最低")),
        "open": _number_or_none(_first_value(latest, "open", "开盘")),
        "amount": _number_or_none(_first_value(latest, "amount", "成交额")),
        "volume": _number_or_none(_first_value(latest, "volume", "成交量")),
        "date": latest["__date"],
        "source": f"akshare.stock_zh_index_daily_em:{symbol}",
    }


def _index_rows(trade_date: str, errors: list[dict[str, str]]) -> list[dict[str, Any]]:
    sina_rows = _sina_index_rows(errors)
    if sina_rows:
        return sina_rows

    targets = [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
    ]
    rows = []
    for symbol, name in targets:
        row = _run_optional_source(
            f"akshare.stock_zh_index_daily_em:{symbol}",
            errors,
            "index_row",
            (symbol, name, trade_date),
        )
        if row:
            rows.append(row)
    return rows


def _market_statistics_from_spot(spot: pd.DataFrame) -> dict[str, int | float | None]:
    if spot.empty or "涨跌幅" not in spot.columns:
        return {
            "up_count": None,
            "down_count": None,
            "flat_count": None,
            "turnover": None,
        }

    pct = pd.to_numeric(spot["涨跌幅"], errors="coerce")
    amount = (
        pd.to_numeric(spot["成交额"], errors="coerce").sum()
        if "成交额" in spot.columns
        else None
    )

    return {
        "up_count": int((pct > 0).sum()),
        "down_count": int((pct < 0).sum()),
        "flat_count": int((pct == 0).sum()),
        "turnover": _number_or_none(amount),
    }


def _sina_symbol_from_code(code: Any) -> str | None:
    text = str(code).strip().zfill(6)
    if not text.isdigit() or len(text) != 6:
        return None
    if text.startswith(("60", "68", "90")):
        return f"sh{text}"
    if text.startswith(("00", "30", "20")):
        return f"sz{text}"
    if text.startswith(("43", "83", "87", "88", "92")):
        return f"bj{text}"
    return None


def _sina_a_spot_statistics() -> dict[str, int | float | None]:
    symbols = _sina_a_stock_symbols()
    if not symbols:
        return {
            "up_count": None,
            "down_count": None,
            "flat_count": None,
            "turnover": None,
        }

    up_count = 0
    down_count = 0
    flat_count = 0
    turnover = 0.0
    valid_count = 0

    for start in range(0, len(symbols), 300):
        batch = symbols[start : start + 300]
        response = requests.get(
            f"https://hq.sinajs.cn/list={','.join(batch)}",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://finance.sina.com.cn/",
            },
            timeout=10,
        )
        response.raise_for_status()
        text = response.content.decode("gbk", errors="ignore")

        for line in text.splitlines():
            if '="' not in line:
                continue
            values = line.split('="', 1)[1].rstrip('";').split(",")
            if len(values) < 10 or not values[0]:
                continue

            current = _number_or_none(values[3])
            previous_close = _number_or_none(values[2])
            amount = _number_or_none(values[9])
            if current is None or previous_close in (None, 0):
                continue

            valid_count += 1
            if current > previous_close:
                up_count += 1
            elif current < previous_close:
                down_count += 1
            else:
                flat_count += 1

            if amount is not None:
                turnover += amount

    return {
        "up_count": up_count if valid_count else None,
        "down_count": down_count if valid_count else None,
        "flat_count": flat_count if valid_count else None,
        "turnover": turnover if valid_count else None,
    }


def _code_column(frame: pd.DataFrame) -> str | None:
    for column in ("code", "证券代码", "A股代码", "代码"):
        if column in frame.columns:
            return column
    return None


def _symbols_from_code_frame(frame: pd.DataFrame) -> list[str]:
    column = _code_column(frame)
    if not column:
        return []
    return [
        symbol
        for symbol in frame[column].map(_sina_symbol_from_code).dropna().tolist()
        if symbol
    ]


def _sina_a_stock_symbols() -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()

    loaders = [
        ak.stock_info_a_code_name,
        lambda: ak.stock_info_sh_name_code(symbol="主板A股"),
        lambda: ak.stock_info_sh_name_code(symbol="科创板"),
        lambda: ak.stock_info_sz_name_code(symbol="A股列表"),
        ak.stock_info_bj_name_code,
    ]

    for loader in loaders:
        try:
            frame = loader()
        except Exception:
            continue
        if frame.empty:
            continue

        for symbol in _symbols_from_code_frame(frame):
            if symbol in seen:
                continue
            seen.add(symbol)
            symbols.append(symbol)

    return symbols


def _turnover_from_indices(index_rows: list[dict[str, Any]]) -> float | None:
    """Use Shanghai + Shenzhen index amounts as a fallback market turnover."""
    names = {"上证指数", "深证成指"}
    amount = 0.0
    count = 0
    for row in index_rows:
        if row.get("name") not in names:
            continue
        value = _number_or_none(row.get("amount"))
        if value is None:
            continue
        amount += value
        count += 1
    return amount if count else None


def _industry_lookup(industry_board: pd.DataFrame) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    if industry_board.empty:
        return lookup

    for _, row in industry_board.iterrows():
        name = _text_or_none(_first_value(row, "板块名称", "名称"))
        if not name:
            continue
        lookup[name] = {
            "change_percent": _number_or_none(_first_value(row, "涨跌幅", "change_percent")),
            "amount": _number_or_none(_first_value(row, "成交额", "amount")),
            "source": "akshare.stock_board_industry_name_em",
        }
    return lookup


def _sector_limit_top(
    limit_up_pool: pd.DataFrame,
    industry_board: pd.DataFrame,
) -> list[dict[str, Any]]:
    if limit_up_pool.empty or "所属行业" not in limit_up_pool.columns:
        return []

    industry_meta = _industry_lookup(industry_board)
    grouped = (
        limit_up_pool.dropna(subset=["所属行业"])
        .groupby("所属行业")
        .size()
        .reset_index(name="limit_up_count")
        .sort_values("limit_up_count", ascending=False)
    )

    rows = []
    for rank, (_, row) in enumerate(grouped.head(10).iterrows(), start=1):
        sector_name = str(row["所属行业"])
        meta = industry_meta.get(sector_name, {})
        rows.append(
            {
                "rank": rank,
                "sector_name": sector_name,
                "name": sector_name,
                "limit_up_count": int(row["limit_up_count"]),
                "change_percent": meta.get("change_percent"),
                "amount": meta.get("amount"),
                "source": meta.get("source") or "akshare.stock_zt_pool_em",
            }
        )
    return rows


def _news_rows() -> list[dict[str, Any]]:
    sina_rows = _sina_news_rows()
    if sina_rows:
        return sina_rows

    if not ENABLE_SLOW_SOURCES:
        return []

    loaders = [
        ("akshare.stock_info_global_cls", ak.stock_info_global_cls),
        ("akshare.stock_info_global_em", ak.stock_info_global_em),
    ]

    for source, loader in loaders:
        try:
            frame = loader()
        except Exception:
            continue
        if frame.empty:
            continue

        rows = []
        for _, row in frame.head(10).iterrows():
            title = _text_or_none(_first_value(row, "标题", "title", "内容"))
            if not title:
                continue
            rows.append(
                {
                    "time": _text_or_none(_first_value(row, "发布时间", "发布日期", "时间", "date")),
                    "date": _text_or_none(_first_value(row, "发布时间", "发布日期", "时间", "date")),
                    "category": _text_or_none(_first_value(row, "类型", "分类")) or "财经",
                    "title": title,
                    "headline": title,
                    "source": source,
                }
            )
        if rows:
            return rows

    return []


def _sina_news_rows() -> list[dict[str, Any]]:
    response = requests.get(
        "https://finance.sina.com.cn/roll/index.d.html",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=8,
    )
    response.raise_for_status()
    text = response.content.decode(response.apparent_encoding or "utf-8", errors="ignore")

    pattern = re.compile(
        r'<a[^>]+href="(?P<url>https?://finance\.sina\.com\.cn/[^"]+)"[^>]*>(?P<title>[^<]{8,80})</a>',
        re.IGNORECASE,
    )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        title = re.sub(r"\s+", " ", match.group("title")).strip()
        if not title or title in seen:
            continue
        seen.add(title)
        rows.append(
            {
                "time": None,
                "date": None,
                "category": "财经",
                "title": title,
                "headline": title,
                "source": "sina.finance.roll",
                "url": match.group("url"),
            }
        )
        if len(rows) >= 10:
            break

    return rows


def _combine_margin_balance() -> list[dict[str, Any]]:
    shanghai = ak.macro_china_market_margin_sh()
    shenzhen = ak.macro_china_market_margin_sz()

    frames = []
    for source, frame in (("sse", shanghai), ("szse", shenzhen)):
        if frame.empty:
            continue
        subset = frame[["日期", "融资融券余额"]].copy()
        subset["date"] = subset["日期"].map(_date_from_value)
        subset["margin_balance"] = subset["融资融券余额"].map(_number_or_none)
        subset["source"] = source
        frames.append(subset[["date", "margin_balance", "source"]])

    if not frames:
        return []

    combined = pd.concat(frames, ignore_index=True)
    grouped = (
        combined.dropna(subset=["date"])
        .groupby("date", as_index=False)["margin_balance"]
        .sum()
        .sort_values("date")
        .tail(760)
    )

    return [
        {
            "date": str(row["date"]),
            "margin_balance": _number_or_none(row["margin_balance"]),
            "source": "akshare:macro_china_market_margin_sh+sz",
        }
        for _, row in grouped.iterrows()
    ]


class AkShareMarketDataProvider:
    """Collect market facts from AKShare interfaces that are available locally."""

    def collect(self, trade_date: str) -> dict[str, Any]:
        errors: list[dict[str, str]] = []
        limit_up_pool = _safe_frame(
            "akshare.stock_zt_pool_em",
            errors,
            lambda: _load_limit_up_pool(trade_date),
        )
        limit_down_pool = _safe_frame(
            "akshare.stock_zt_pool_dtgc_em",
            errors,
            lambda: _load_limit_down_pool(trade_date),
        )

        if limit_up_pool.empty:
            return _empty_market_daily(trade_date, errors)

        margin_balance = _safe_list(
            "akshare.macro_china_market_margin_sh+sz",
            errors,
            _combine_margin_balance,
        )
        index_data = _index_rows(trade_date, errors)

        sina_statistics = _run_optional_source(
            "sina.hq.sinajs.cn:a_spot_batch",
            errors,
            "sina_a_spot_stats",
            timeout=45,
        )
        spot_statistics = (
            sina_statistics
            if isinstance(sina_statistics, dict)
            else {
                "up_count": None,
                "down_count": None,
                "flat_count": None,
                "turnover": None,
            }
        )
        if spot_statistics["up_count"] is None and ENABLE_SLOW_SOURCES:
            a_spot = _run_optional_source(
                "akshare.stock_zh_a_spot_em",
                errors,
                "a_spot",
            )
            if a_spot is None:
                a_spot = pd.DataFrame()
            spot_statistics = _market_statistics_from_spot(a_spot)

        turnover = spot_statistics.pop("turnover")
        if turnover is None:
            turnover = _turnover_from_indices(index_data)

        industry_board = pd.DataFrame()
        if ENABLE_SLOW_SOURCES:
            industry_board = _run_optional_source(
                "akshare.stock_board_industry_name_em",
                errors,
                "industry_board",
            )
            if industry_board is None:
                industry_board = pd.DataFrame()

        return {
            "schema_version": "1.0",
            "date": trade_date,
            "turnover": turnover,
            "total_turnover": turnover,
            "indices": index_data,
            "index_data": index_data,
            "shanghai_index": index_data[0] if index_data else None,
            "market_statistics": {
                "up_count": spot_statistics["up_count"],
                "down_count": spot_statistics["down_count"],
                "flat_count": spot_statistics["flat_count"],
                "limit_up_count": int(len(limit_up_pool)),
                "limit_down_count": int(len(limit_down_pool)),
            },
            "limit_chain_stocks": _limit_chain_stocks(limit_up_pool),
            "sectors": _sector_limit_top(limit_up_pool, industry_board),
            "margin_balance": margin_balance,
            "news": _run_optional_source(
                "akshare.stock_info_global_*",
                errors,
                "news_rows",
                timeout=12,
            )
            or [],
            "sources": [
                "akshare.stock_zt_pool_em",
                "akshare.stock_zt_pool_dtgc_em",
                "akshare.stock_zh_a_spot_em",
                "akshare.stock_board_industry_name_em",
                "akshare.stock_zh_index_daily_em",
                "sina.hq.sinajs.cn",
                "sina.finance.roll",
                "akshare.macro_china_market_margin_sh",
                "akshare.macro_china_market_margin_sz",
            ],
            "source_errors": errors,
        }
