"""Fifteenth Five-Year Plan theme radar service."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.storage.repository import (
    get_concept_daily,
    get_latest_market_report,
    get_market_report,
    get_plan2030_theme_daily,
    get_plan2030_theme_stocks,
    get_stock_daily,
    get_stock_snapshot_daily,
)

THEME_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "plan2030_themes.json"


def _today() -> str:
    return datetime.now().date().isoformat()


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _avg(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return round(sum(clean) / len(clean), 2) if clean else None


def _sum(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return round(sum(clean), 2) if clean else None


def _amount_yi(value: Any) -> float | None:
    number = _number(value)
    if number is None:
        return None
    return number / 100_000_000 if abs(number) > 1_000_000 else number


def _load_themes() -> list[dict[str, Any]]:
    try:
        with THEME_CONFIG_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _theme_by_id(themes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(theme.get("id")): theme for theme in themes if theme.get("id")}


def _risk_notes(theme: dict[str, Any], has_report: bool, has_theme_row: bool) -> list[str]:
    if not has_report:
        return ["所选日期暂无市场日报，请先完成该交易日同步"]
    if not has_theme_row:
        return ["该主题暂无结构化分析结果，请重新同步该交易日生成主题日表"]

    notes: list[str] = []
    if int(theme.get("limitUp") or 0) == 0:
        notes.append("暂未在涨停池中形成有效映射")
    if theme.get("change") is not None and theme["change"] < 0:
        notes.append("概念表现为负，政策热度尚未获得价格确认")
    if theme.get("inflow") is not None and theme["inflow"] < 0:
        notes.append("主题资金净流出，注意冲高回落风险")
    return notes or ["主题热度中性，继续观察资金流和龙头持续性"]


def _news_events(data: dict[str, Any] | None, keywords: list[str]) -> list[str]:
    events: list[str] = []
    for item in _as_list((data or {}).get("news")):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("headline") or "")
        if title and any(keyword.lower() in title.lower() for keyword in keywords):
            events.append(title)
        if len(events) >= 3:
            break
    return events


def _matched_concepts(concept_rows: list[dict[str, Any]], keywords: list[str]) -> list[str]:
    matched: list[str] = []
    for row in concept_rows:
        name = str(row.get("name") or "")
        if name and any(keyword.lower() in name.lower() for keyword in keywords):
            matched.append(name)
        if len(matched) >= 5:
            break
    return matched


def _stock_identity(stock: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": stock.get("code") or "",
        "name": stock.get("name") or "",
        "role": stock.get("role") or stock.get("industry") or "主题核心",
        "change": _number(stock.get("change")),
        "inflow": _number(stock.get("inflow")),
        "freeFloatMarketCap": _amount_yi(stock.get("freeFloatMarketCap")),
        "totalMarketCap": _amount_yi(stock.get("totalMarketCap")),
        "turnoverRate": _number(stock.get("turnoverRate")),
        "sealAmount": _amount_yi(stock.get("sealAmount")),
    }


def _core_stocks(
    snapshot_rows: list[dict[str, Any]],
    keywords: list[str],
    limit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not snapshot_rows:
        return []

    limit_codes = {str(row.get("code")) for row in limit_rows if row.get("code")}

    # Pre-filter by keyword matching on stock name
    matched = [
        row
        for row in snapshot_rows
        if any(keyword.lower() in str(row.get("name") or "").lower() for keyword in keywords)
    ]
    if not matched:
        return []

    # Prefer sorting by market cap; fall back to amount (成交额) when unavailable
    has_market_cap = any(_number(row.get("freeFloatMarketCap")) is not None for row in matched)
    if has_market_cap:
        candidates = [row for row in matched if _number(row.get("freeFloatMarketCap")) is not None]
        candidates.sort(
            key=lambda item: (
                _number(item.get("freeFloatMarketCap")) or 0,
                _number(item.get("totalMarketCap")) or 0,
            ),
            reverse=True,
        )
    else:
        candidates = matched
        candidates.sort(
            key=lambda item: _number(item.get("amount")) or 0,
            reverse=True,
        )
    return [
        {
            **_stock_identity(row),
            "isLimitUp": str(row.get("code")) in limit_codes,
        }
        for row in candidates[:5]
    ]


def _empty_theme(config: dict[str, Any], data: dict[str, Any] | None, has_report: bool) -> dict[str, Any]:
    keywords = [str(item) for item in config.get("keywords", [])]
    return {
        "id": config.get("id"),
        "name": config.get("name"),
        "axis": config.get("axis"),
        "score": 0,
        "status": "待验证",
        "change": None,
        "turnover": None,
        "inflow": None,
        "limitUp": 0,
        "continuity": None,
        "concepts": config.get("concepts", []),
        "leaders": [],
        "coreStocks": [],
        "catalysts": _news_events(data, keywords),
        "risks": _risk_notes({"limitUp": 0}, has_report, False),
        "matchedSectors": [],
    }


def get_plan2030_daily(trade_date: str | None = None) -> dict[str, Any]:
    report = get_market_report(trade_date) if trade_date else get_latest_market_report()
    has_report = bool(report and isinstance(report.get("data"), dict))
    data = report.get("data") if has_report else None
    data_date = trade_date or (report.get("date") if report else _today())

    themes_config = _load_themes()
    config_lookup = _theme_by_id(themes_config)
    theme_rows = get_plan2030_theme_daily(data_date)
    stock_rows = get_plan2030_theme_stocks(data_date)
    concept_rows = get_concept_daily(data_date)
    all_stock_rows = get_stock_daily(data_date)
    stock_snapshot_rows = get_stock_snapshot_daily(data_date)
    stock_lookup = {
        str(row.get("code")): row
        for row in all_stock_rows
        if row.get("code")
    }
    stocks_by_theme: dict[str, list[dict[str, Any]]] = {}
    for row in stock_rows:
        stocks_by_theme.setdefault(str(row.get("themeId")), []).append(row)

    materialized_ids = set()
    themes: list[dict[str, Any]] = []
    for row in theme_rows:
        theme_id = str(row.get("id"))
        config = config_lookup.get(theme_id, {})
        keywords = [str(item) for item in config.get("keywords", [])]
        core_keywords = [*keywords, *[str(item) for item in config.get("concepts", [])]]
        leaders = [
            _stock_identity(
                {
                    **item,
                    **{
                        key: value
                        for key, value in (stock_lookup.get(str(item.get("code"))) or {}).items()
                        if value is not None
                    },
                    "role": item.get("role") or "主题映射",
                    "change": item.get("change"),
                    "inflow": item.get("inflow"),
                }
            )
            for item in stocks_by_theme.get(theme_id, [])
        ][:5]
        leader_stock_rows = [
            stock_lookup.get(str(leader.get("code")))
            for leader in leaders
            if leader.get("code")
        ]
        leader_stock_rows = [row for row in leader_stock_rows if isinstance(row, dict)]
        leader_change = _avg([_number(item.get("change")) for item in leaders])
        leader_amount = _sum([_amount_yi(row.get("amount")) for row in leader_stock_rows])
        leader_continuity_values = [
            int(row["chainDays"])
            for row in leader_stock_rows
            if isinstance(row.get("chainDays"), (int, float))
        ]
        theme = {
            "id": theme_id,
            "name": row.get("name") or config.get("name"),
            "axis": row.get("axis") or config.get("axis"),
            "score": int(row.get("score") or 0),
            "status": row.get("status") or "待验证",
            "change": _number(row.get("change")) if row.get("change") is not None else leader_change,
            "turnover": _number(row.get("turnover")) if row.get("turnover") is not None else leader_amount,
            "inflow": _number(row.get("inflow")),
            "limitUp": int(row.get("limitUp") or 0),
            "continuity": max(leader_continuity_values) if leader_continuity_values else None,
            "concepts": config.get("concepts", []),
            "leaders": leaders,
            "coreStocks": _core_stocks(stock_snapshot_rows, core_keywords, leaders),
            "catalysts": _news_events(data, keywords),
            "matchedSectors": _matched_concepts(concept_rows, keywords),
        }
        theme["risks"] = _risk_notes(theme, has_report, True)
        themes.append(theme)
        materialized_ids.add(theme_id)

    for config in themes_config:
        theme_id = str(config.get("id"))
        if theme_id not in materialized_ids:
            themes.append(_empty_theme(config, data, has_report))

    themes.sort(key=lambda item: item["score"], reverse=True)
    inflows = [item["inflow"] for item in themes if item.get("inflow") is not None]
    news_event_count = sum(len(item["catalysts"]) for item in themes)

    return {
        "date": data_date,
        "sourceDate": data.get("date") if isinstance(data, dict) else None,
        "usingFallback": not has_report,
        "themes": themes,
        "summary": {
            "themeCount": len(themes),
            "avgScore": round(sum(item["score"] for item in themes) / len(themes)) if themes else 0,
            "limitUpCount": sum(item["limitUp"] for item in themes),
            "inflow": round(sum(inflows), 2) if inflows else None,
        },
        "dataCoverage": {
            "marketReport": has_report,
            "themeConfig": bool(themes_config),
            "conceptQuotes": bool(concept_rows),
            "fundFlow": any(row.get("inflow") is not None for row in concept_rows),
            "newsKeywordMatch": news_event_count > 0,
            "stockDaily": bool(all_stock_rows),
            "stockSnapshot": bool(stock_snapshot_rows),
            "themeDaily": bool(theme_rows),
        },
        "diagnostics": {
            "conceptRows": len(concept_rows),
            "stockRows": len(all_stock_rows),
            "stockSnapshotRows": len(stock_snapshot_rows),
            "themeRows": len(theme_rows),
            "themeStockRows": len(stock_rows),
            "newsEventCount": news_event_count,
        },
    }
