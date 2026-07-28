"""AKShare-backed market data provider for AIMS."""

from __future__ import annotations

import logging
import re
import os
import socket
from datetime import datetime
from multiprocessing import get_context
from typing import Any

import akshare as ak
import pandas as pd
import requests

from backend.services.trade_calendar import previous_trade_date

logger = logging.getLogger(__name__)


PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


for proxy_key in PROXY_ENV_KEYS:
    os.environ.pop(proxy_key, None)

socket.setdefaulttimeout(15)
_REQUEST_WITHOUT_DEFAULT_TIMEOUT = requests.sessions.Session.request


def _request_with_default_timeout(self, method, url, **kwargs):
    kwargs.setdefault("timeout", 15)
    self.trust_env = False
    kwargs.setdefault("proxies", {})
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


def _today_iso() -> str:
    return datetime.now().date().isoformat()


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


def _log_api(platform: str, trade_date: str, api: str, result: str) -> None:
    """Structured log for API requests: [平台] 日期 | 接口 | 结果"""
    logger.info("[%s] %s | %s | %s", platform, trade_date, api, result)


def _log(msg: str, *args: Any) -> None:
    """Short-hand for internal detail log."""
    logger.info("| %s", msg % args if args else msg)


def _load_limit_up_pool(trade_date: str) -> pd.DataFrame:
    result = ak.stock_zt_pool_em(date=_date_compact(trade_date))
    _log_api("东方财富", trade_date, "stock_zt_pool_em",
             f"✅ 成功 涨停池{len(result)}只" if not result.empty else "❌ 失败 返回空")
    return result


def _load_limit_down_pool(trade_date: str) -> pd.DataFrame:
    result = ak.stock_zt_pool_dtgc_em(date=_date_compact(trade_date))
    _log_api("东方财富", trade_date, "stock_zt_pool_dtgc_em",
             f"✅ 成功 跌停池{len(result)}只" if not result.empty else "✅ 成功 跌停池0只")
    return result


def _load_a_spot() -> pd.DataFrame:
    result = ak.stock_zh_a_spot_em()
    # trade_date not available here; caller will log
    return result


def _load_industry_board() -> pd.DataFrame:
    _log("请求东方财富行业板块 stock_board_industry_name_em")
    return ak.stock_board_industry_name_em()


def _worker(source_name: str, args: tuple[Any, ...], queue) -> None:
    functions = {
        "index_row": _index_row,
        "a_spot": _load_a_spot,
        "sina_a_spot_stats": _sina_a_spot_statistics,
        "industry_board": _load_industry_board,
        "news_rows": _news_rows,
        "tencent_snapshot": _tencent_stock_snapshot_rows,
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
    _log("子进程启动 source=%s timeout=%ds", source_name, timeout)
    context = get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_worker, args=(source_name, args, queue))
    process.start()
    process.join(timeout)

    if process.is_alive():
        process.kill()
        process.join()
        _log("子进程超时 source=%s timeout=%ds", source_name, timeout)
        errors.append({"source": source, "error": f"TimeoutError: exceeded {timeout}s"})
        return None

    if queue.empty():
        if process.exitcode not in (0, None):
            _log("子进程异常退出 source=%s exit_code=%s", source_name, process.exitcode)
            errors.append({"source": source, "error": f"ProcessError: exit code {process.exitcode}"})
        else:
            _log("子进程无返回 source=%s", source_name)
        return None

    result = queue.get()
    if result.get("ok"):
        _log("子进程完成 source=%s", source_name)
        return result.get("value")

    _log("子进程失败 source=%s error=%s", source_name, str(result.get("error", "unknown error"))[:120])
    errors.append({"source": source, "error": result.get("error", "unknown error")})
    return None


def _safe_frame(source: str, errors: list[dict[str, str]], loader) -> pd.DataFrame:
    try:
        result = loader()
        if hasattr(result, "empty"):
            _log("数据加载成功 source=%s rows=%d", source, len(result) if hasattr(result, "__len__") else -1)
            return result
    except Exception as exc:  # noqa: BLE001 - each source should fail independently.
        _log("数据加载失败 source=%s error=%s", source, str(exc)[:150])
        errors.append({"source": source, "error": f"{type(exc).__name__}: {exc}"})
    return pd.DataFrame()


def _safe_list(source: str, errors: list[dict[str, str]], loader) -> list[dict[str, Any]]:
    try:
        result = loader()
        _log("列表数据加载成功 source=%s count=%d", source, len(result))
        return result
    except Exception as exc:  # noqa: BLE001 - each source should fail independently.
        _log("列表数据加载失败 source=%s error=%s", source, str(exc)[:150])
        errors.append({"source": source, "error": f"{type(exc).__name__}: {exc}"})
    return []


def _is_bj_code(code: Any) -> bool:
    """Check if a stock code belongs to 北交所."""
    code_str = str(code or "").strip().zfill(6)
    return code_str[:2] in ("92", "43", "83", "87", "88")


def _limit_chain_stocks(limit_up_pool: pd.DataFrame) -> list[dict[str, Any]]:
    if limit_up_pool.empty:
        _log("涨停池为空，连板股列表跳过")
        return []

    rows = []
    sorted_pool = limit_up_pool.sort_values(
        by="连板数",
        ascending=False,
        na_position="last",
    )

    for _, row in sorted_pool.head(50).iterrows():
        stock_code = str(row.get("代码", ""))
        if _is_bj_code(stock_code):
            continue
        rows.append(
            {
                "stock_code": stock_code,
                "stock_name": str(row.get("名称", "")),
                "chain_days": _number_or_none(row.get("连板数")),
                "change_pct": _number_or_none(row.get("涨跌幅")),
                "amount": _number_or_none(row.get("成交额")),
                "free_float_market_cap": _number_or_none(row.get("流通市值")),
                "total_market_cap": _number_or_none(row.get("总市值")),
                "turnover_rate": _number_or_none(row.get("换手率")),
                "seal_amount": _number_or_none(row.get("封板资金")),
                "detail": _text_or_none(row.get("涨停统计")),
                "industry": _text_or_none(row.get("所属行业")),
                "reason": _text_or_none(row.get("所属行业")),
            }
        )

    return rows


def _record_rows(frame: pd.DataFrame, source: str) -> list[dict[str, Any]]:
    if frame.empty:
        return []

    rows = []
    for _, row in frame.iterrows():
        record = row.to_dict()
        record["source"] = source
        rows.append(record)
    return rows


def _stock_snapshot_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []

    rows = []
    for _, row in frame.iterrows():
        stock_code = str(row.get("代码", "")).strip().zfill(6)
        stock_name = _text_or_none(row.get("名称"))
        if not stock_code or not stock_name:
            continue
        rows.append(
            {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "close": _number_or_none(row.get("最新价")),
                "change_pct": _number_or_none(row.get("涨跌幅")),
                "amount": _number_or_none(row.get("成交额")),
                "free_float_market_cap": _number_or_none(row.get("流通市值")),
                "total_market_cap": _number_or_none(row.get("总市值")),
                "turnover_rate": _number_or_none(row.get("换手率")),
                "source": "akshare.stock_zh_a_spot_em",
            }
        )
    return rows


def _concept_fund_flow_rows(errors: list[dict[str, str]]) -> list[dict[str, Any]]:
    _log("加载概念资金流数据...")
    loaders = [
        ("akshare.stock_fund_flow_concept:即时", lambda: ak.stock_fund_flow_concept(symbol="即时")),
        ("akshare.stock_fund_flow_concept:即时排名", lambda: ak.stock_fund_flow_concept(symbol="即时排名")),
        (
            "akshare.stock_sector_fund_flow_rank:概念资金流",
            lambda: ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="概念资金流"),
        ),
    ]
    results = []
    for source, loader in loaders:
        frame = _safe_frame(source, errors, loader)
        if not frame.empty:
            rows = _record_rows(frame, source)
            results.extend(rows)
            _log("概念资金流: %s %d条", source, len(rows))
    if not results:
        _log("概念资金流: 所有源均不可用")
    return results


def _empty_market_daily(trade_date: str, errors: list[dict[str, str]]) -> dict[str, Any]:
    _log("涨停池为空，返回空日报 trade_date=%s", trade_date)
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
        "concept_fund_flow": [],
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
        "s_sh000688": "科创50",
        "s_sh000300": "沪深300",
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


def _tencent_index_rows(errors: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Fetch index data from Tencent API (qt.gtimg.cn) as fallback."""
    symbols = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
        "sh000688": "科创50",
        "sh000300": "沪深300",
    }
    url = f"http://qt.gtimg.cn/q={','.join(symbols.keys())}"

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        response.raise_for_status()
    except Exception as exc:
        errors.append({"source": "tencent.qt.gtimg.cn:index", "error": f"{type(exc).__name__}: {exc}"})
        return []

    rows: list[dict[str, Any]] = []
    for line in response.text.strip().split("\n"):
        line = line.strip()
        if '="' not in line:
            continue
        key = line.split('="', 1)[0].replace("v_", "")
        name = symbols.get(key)
        if not name:
            continue

        fields = line.split('="', 1)[1].rstrip('";').split("~")
        if len(fields) < 35:
            continue

        close = _number_or_none(fields[3])
        change_pct = _number_or_none(fields[32])
        volume = _number_or_none(fields[6])
        high = _number_or_none(fields[33])
        low = _number_or_none(fields[34])
        open_price = _number_or_none(fields[5])
        amount_wan = _number_or_none(fields[37])
        amount = amount_wan * 10000 if amount_wan is not None else None

        rows.append(
            {
                "name": name,
                "index_name": name,
                "close": close,
                "change_pct": change_pct,
                "high": high,
                "low": low,
                "open": open_price,
                "amount": amount,
                "volume": volume,
                "source": f"tencent.qt.gtimg.cn:{key}",
            }
        )

    return rows


def _index_rows(
    trade_date: str,
    errors: list[dict[str, str]],
    *,
    use_realtime: bool = False,
) -> list[dict[str, Any]]:
    if use_realtime:
        sina_rows = _sina_index_rows(errors)
        if sina_rows:
            _log_api("新浪", trade_date, "hq.sinajs.cn:index", f"✅ 成功 {len(sina_rows)}条")
            return sina_rows

    targets = [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
        ("sh000688", "科创50"),
        ("sh000300", "沪深300"),
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
        else:
            _log_api("东方财富", trade_date, f"stock_zh_index_daily_em:{symbol}", "❌ 失败")
    if rows:
        _log_api("东方财富", trade_date, "stock_zh_index_daily_em", f"✅ 成功 {len(rows)}/{len(targets)}条")
        return rows

    # Final fallback: Tencent API
    _log("东方财富指数失败，尝试腾讯API...")
    tencent_rows = _tencent_index_rows(errors)
    if tencent_rows:
        _log_api("腾讯", trade_date, "qt.gtimg.cn:index", f"✅ 成功 {len(tencent_rows)}条")
    return tencent_rows


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
    _log("获取全A股代码列表（新浪源）...")
    symbols: list[str] = []
    seen: set[str] = set()

    loaders = [
        ("ak.stock_info_a_code_name", ak.stock_info_a_code_name),
        ("ak.stock_info_sh_name_code(主板A股)", lambda: ak.stock_info_sh_name_code(symbol="主板A股")),
        ("ak.stock_info_sh_name_code(科创板)", lambda: ak.stock_info_sh_name_code(symbol="科创板")),
        ("ak.stock_info_sz_name_code(A股列表)", lambda: ak.stock_info_sz_name_code(symbol="A股列表")),
        ("ak.stock_info_bj_name_code", ak.stock_info_bj_name_code),
    ]

    for source_name, loader in loaders:
        try:
            frame = loader()
            if frame.empty:
                continue
            count_before = len(symbols)
            for symbol in _symbols_from_code_frame(frame):
                if symbol in seen:
                    continue
                seen.add(symbol)
                symbols.append(symbol)
            _log("  源 %s: 新增 %d 只股票", source_name, len(symbols) - count_before)
        except Exception:
            _log("  源 %s: 不可用（跳过）", source_name)
            continue

    _log("全A股代码列表获取完成: 共 %d 只", len(symbols))
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

    # Filter out 北交所 stocks
    pool = limit_up_pool.copy()
    if "代码" in pool.columns:
        pool = pool[~pool["代码"].astype(str).apply(_is_bj_code)]

    industry_meta = _industry_lookup(industry_board)
    grouped = (
        pool.dropna(subset=["所属行业"])
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


def _tencent_stock_snapshot_rows() -> list[dict[str, Any]]:
    """Fetch full A-share stock snapshot with market cap from Tencent API.

    Uses qt.gtimg.cn which returns: price, change%, amount,
    total market cap, free float market cap, turnover rate.
    Designed to be called via _run_optional_source subprocess worker.

    Raises RuntimeError on failure so the subprocess can report it.
    """
    # Subprocess needs its own logging config; use FileHandler with UTF-8 if set
    if not logger.handlers:
        log_file = os.environ.get("AIMS_LOG_FILE")
        if log_file:
            handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
            handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
            ))
            logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
                force=True,
            )
    _log("腾讯API: 从新浪获取股票列表...")
    sina_spot = ak.stock_zh_a_spot()
    if sina_spot.empty:
        raise RuntimeError("No stock symbols available from Sina API")

    _log("腾讯API: 新浪返回 %d 只股票，转换代码格式...", len(sina_spot))
    # Note: actual trade_date is not passed to subprocess; caller will log summary
    rows: list[dict[str, Any]] = []
    batch_size = 200

    for _, row in sina_spot.iterrows():
        code_raw = str(row.get("代码", "")).strip()
        name = row.get("名称", "")
        if not code_raw or not name:
            continue

        # Convert to Tencent symbol format (sh600519 / sz000001 / bj...)
        tencent_code = code_raw
        if len(tencent_code) == 8 and tencent_code[:2] in ("sh", "sz", "bj"):
            stock_code = tencent_code[-6:]  # Already prefixed, extract last 6 chars
        elif len(tencent_code) <= 6:
            stock_code = tencent_code.zfill(6)
            if stock_code.startswith(("60", "68", "90")):
                tencent_code = f"sh{stock_code}"
            elif stock_code.startswith(("00", "30", "20")):
                tencent_code = f"sz{stock_code}"
            elif stock_code.startswith(("43", "83", "87", "88", "92")):
                tencent_code = f"bj{stock_code}"
            else:
                continue  # Unknown market, skip
        else:
            continue

        rows.append({
            "tencent_symbol": tencent_code,
            "stock_code": stock_code,
            "stock_name": str(name).strip(),
        })

    if not rows:
        raise RuntimeError("No valid stock codes found from Sina API")

    _log("腾讯API: 转换完成，共 %d 只，分 %d 批查询...", len(rows), (len(rows) + batch_size - 1) // batch_size)

    # Batch query Tencent API for market cap and other fields
    result_rows: list[dict[str, Any]] = []
    total_batches = (len(rows) + batch_size - 1) // batch_size
    for batch_idx, start in enumerate(range(0, len(rows), batch_size), 1):
        batch = rows[start:start + batch_size]
        query = ",".join(item["tencent_symbol"] for item in batch)
        response = requests.get(
            f"http://qt.gtimg.cn/q={query}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )
        response.raise_for_status()

        parsed_count = 0
        for raw_line in response.text.strip().split("\n"):
            line = raw_line.strip()
            if '="' not in line:
                continue
            raw = line.split('="', 1)[1].rstrip('";')
            fields = raw.split("~")
            if len(fields) < 46:
                continue

            tcode = fields[2].strip()
            # Find the matching meta entry
            meta = next((m for m in batch if m["tencent_symbol"].endswith(tcode)), None)
            if meta is None:
                continue

            close = _number_or_none(fields[3])
            change_pct = _number_or_none(fields[32])
            amount_wan = _number_or_none(fields[37])
            amount = amount_wan * 10000 if amount_wan is not None else None
            total_mv_yi = _number_or_none(fields[44])
            float_mv_yi = _number_or_none(fields[45])
            total_mv = total_mv_yi * 100000000 if total_mv_yi is not None else None
            float_mv = float_mv_yi * 100000000 if float_mv_yi is not None else None
            turnover_rate = _number_or_none(fields[38])

            result_rows.append({
                "stock_code": meta["stock_code"],
                "stock_name": meta["stock_name"],
                "close": close,
                "change_pct": change_pct,
                "amount": amount,
                "free_float_market_cap": float_mv,
                "total_market_cap": total_mv,
                "turnover_rate": turnover_rate,
                "source": "tencent.qt.gtimg.cn",
            })
            parsed_count += 1

        _log("腾讯API: 批次 %d/%d 完成 %d只", batch_idx, total_batches, parsed_count)

    if not result_rows:
        raise RuntimeError("No data returned from Tencent API")

    _log("腾讯API: 全部完成 %d只 (含市值)", len(result_rows))
    return result_rows


def _tencent_market_statistics(snapshot_rows: list[dict[str, Any]]) -> dict[str, int | float | None]:
    """Calculate market statistics from Tencent snapshot data."""
    up_count = 0
    down_count = 0
    flat_count = 0
    turnover = 0.0

    for row in snapshot_rows:
        change_pct = row.get("change_pct")
        if change_pct is not None:
            if change_pct > 0:
                up_count += 1
            elif change_pct < 0:
                down_count += 1
            else:
                flat_count += 1
        amount = row.get("amount")
        if amount is not None:
            turnover += amount

    return {
        "up_count": up_count if up_count + down_count + flat_count > 0 else None,
        "down_count": down_count if up_count + down_count + flat_count > 0 else None,
        "flat_count": flat_count if up_count + down_count + flat_count > 0 else None,
        "turnover": turnover if turnover > 0 else None,
    }


def _combine_margin_balance() -> list[dict[str, Any]]:
    _log("合并融资融券余额数据（上海+深圳）...")
    shanghai = ak.macro_china_market_margin_sh()
    shenzhen = ak.macro_china_market_margin_sz()
    _log("融资融券: 上海%d条 深圳%d条", len(shanghai), len(shenzhen))

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
        _log_api("数据采集器", trade_date, "=== 开始同步 ===", "")
        errors: list[dict[str, str]] = []
        is_today = trade_date == _today_iso()
        is_latest_snapshot_date = is_today or trade_date == previous_trade_date(_today_iso())
        _log("日期判断: is_today=%s is_latest_snapshot_date=%s", is_today, is_latest_snapshot_date)

        _log("加载涨停/跌停池...")
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
            _log_api("数据采集器", trade_date, "涨停池", "❌ 为空 - 非交易日或数据不可用")
            return _empty_market_daily(trade_date, errors)

        _log("加载融资融券...")
        margin_balance = _safe_list(
            "akshare.macro_china_market_margin_sh+sz",
            errors,
            _combine_margin_balance,
        )
        if margin_balance:
            _log_api("东方财富", trade_date, "macro_china_market_margin_sh+sz",
                     f"✅ 成功 {len(margin_balance)}条")

        _log("加载全A股行情快照（腾讯API）...")
        tencent_snapshot: list[dict[str, Any]] | None = None
        snapshot_source = ""
        if is_latest_snapshot_date:
            try:
                _log("腾讯API: 直接采集（内联，约30s）...")
                tencent_raw = _tencent_stock_snapshot_rows()
                if tencent_raw:
                    tencent_snapshot = tencent_raw
                    snapshot_source = "tencent"
                    _log_api("腾讯API", trade_date, "qt.gtimg.cn:stock_snapshot",
                             f"✅ 成功 {len(tencent_raw)}只（含市值）")
                else:
                    _log_api("腾讯API", trade_date, "qt.gtimg.cn:stock_snapshot", "❌ 返回空")
            except Exception as exc:
                _log_api("腾讯API", trade_date, "qt.gtimg.cn:stock_snapshot",
                         f"❌ {type(exc).__name__}: {str(exc)[:100]}")
        else:
            _log("非最新交易日，跳过全A行情快照")

        _log("加载指数数据...")
        index_data = _index_rows(trade_date, errors, use_realtime=is_today)

        _log("计算涨跌统计...")
        sina_statistics = (
            _run_optional_source(
                "sina.hq.sinajs.cn:a_spot_batch",
                errors,
                "sina_a_spot_stats",
                timeout=45,
            )
            if is_latest_snapshot_date
            else None
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
        if spot_statistics["up_count"] is None:
            if tencent_snapshot:
                _log_api("腾讯API", trade_date, "market_statistics", "从快照计算")
                spot_statistics = _tencent_market_statistics(tencent_snapshot)
            else:
                _log_api("数据采集器", trade_date, "market_statistics", "⚠️ 无数据")
        else:
            _log_api("新浪", trade_date, "hq.sinajs.cn:statistics",
                     f"✅ 涨{spot_statistics.get('up_count')} 跌{spot_statistics.get('down_count')} 平{spot_statistics.get('flat_count')}")

        turnover = spot_statistics.pop("turnover")
        if turnover is None:
            turnover = _turnover_from_indices(index_data)
        _log("成交额=%s", turnover)

        _log("加载行业板块...")
        industry_board = pd.DataFrame()
        if is_today and ENABLE_SLOW_SOURCES:
            industry_board = _run_optional_source(
                "akshare.stock_board_industry_name_em",
                errors,
                "industry_board",
            )
            if industry_board is None:
                industry_board = pd.DataFrame()
        if not industry_board.empty:
            _log_api("东方财富", trade_date, "stock_board_industry_name_em",
                     f"✅ {len(industry_board)}个行业")
        else:
            _log_api("东方财富", trade_date, "stock_board_industry_name_em", "⏭️ 跳过")

        # 计算涨跌幅>=9%和<=-9%的股票数量（排除北交所）
        if tencent_snapshot:
            limit_up_ge_9 = sum(
                1 for s in tencent_snapshot
                if (s.get('change_pct') or 0) >= 9
                and not str(s.get('stock_code', '') or '')[:2] in ('92', '43', '83', '87', '88')
            )
            limit_down_le_neg9 = sum(
                1 for s in tencent_snapshot
                if (s.get('change_pct') or 0) <= -9
                and not str(s.get('stock_code', '') or '')[:2] in ('92', '43', '83', '87', '88')
            )
        else:
            limit_up_ge_9 = int(len(limit_up_pool))
            limit_down_le_neg9 = int(len(limit_down_pool))
        _log("涨跌幅>=9%%: %d 跌跌幅>=9%%: %d (已排除北交所)", limit_up_ge_9, limit_down_le_neg9)

        _log("组装日报...")
        limit_chain = _limit_chain_stocks(limit_up_pool)
        snapshot = tencent_snapshot or []
        sectors = _sector_limit_top(limit_up_pool, industry_board)
        concept_flow = _concept_fund_flow_rows(errors) if is_latest_snapshot_date else []

        _log("加载财经新闻...")
        news = (
            _run_optional_source(
                "akshare.stock_info_global_*",
                errors,
                "news_rows",
                timeout=12,
            )
            or []
        ) if is_latest_snapshot_date else []

        _log_api("数据采集器", trade_date, "=== 同步完成 ===",
                 f"涨停{len(limit_up_pool)}只 跌停{len(limit_down_pool)}只 "
                 f"快照{len(snapshot)}只({snapshot_source or '无'}) "
                 f"指数{len(index_data)}条 概念{len(concept_flow)}条 "
                 f"两融{len(margin_balance)}条 新闻{len(news)}条")
        _log("涨:%s 跌:%s 平:%s | 涨停:%s 跌停:%s | 成交额:%s",
             spot_statistics.get("up_count"), spot_statistics.get("down_count"), spot_statistics.get("flat_count"),
             spot_statistics.get("limit_up_count"), spot_statistics.get("limit_down_count"), turnover)
        if errors:
            _log("采集过程中的错误/警告 (%d 条):", len(errors))
            for e in errors:
                _log("  [%s] %s", e.get("source", "?"), str(e.get("error", ""))[:150])

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
                "limit_up_count": limit_up_ge_9,
                "limit_down_count": limit_down_le_neg9,
            },
            "limit_chain_stocks": limit_chain,
            "stock_snapshot": snapshot,
            "sectors": sectors,
            "concept_fund_flow": concept_flow,
            "margin_balance": margin_balance,
            "news": news,
            "sources": [
                "akshare.stock_zt_pool_em",
                "akshare.stock_zt_pool_dtgc_em",
                "akshare.stock_zh_a_spot_em",
                "akshare.stock_board_industry_name_em",
                "akshare.stock_fund_flow_concept",
                "akshare.stock_zh_index_daily_em",
                "sina.hq.sinajs.cn",
                "sina.finance.roll",
                "akshare.macro_china_market_margin_sh",
                "akshare.macro_china_market_margin_sz",
            ],
            "source_errors": errors,
        }
