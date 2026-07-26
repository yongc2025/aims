"""Repository functions for market data persistence."""

import json
from pathlib import Path
from datetime import datetime
from .database import get_connection


PLAN_THEME_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "plan2030_themes.json"


def _number_or_none(value):
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_list(value):
    return value if isinstance(value, list) else []


def _text_or_none(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_value(record: dict, *keys: str):
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def _load_plan_themes() -> list[dict]:
    try:
        with PLAN_THEME_CONFIG_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _contains_keyword(record: dict, keywords: list[str], fields: tuple[str, ...]) -> bool:
    haystack = " ".join(str(record.get(field) or "") for field in fields).lower()
    return any(keyword.lower() in haystack for keyword in keywords)


def _average(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return round(sum(clean) / len(clean), 2) if clean else None


def _sum_or_none(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return round(sum(clean), 2) if clean else None


def _plan_status(score: int, limit_up_count: int, inflow: float | None) -> str:
    if score >= 85 and limit_up_count >= 8:
        return "高潮"
    if score >= 60 and (limit_up_count >= 4 or (inflow or 0) > 0):
        return "扩散"
    if score >= 30 or limit_up_count:
        return "启动"
    return "待验证"


def _json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def start_sync_run(trade_date: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sync_runs (trade_date, status)
        VALUES (?, ?)
        """,
        (trade_date, "running"),
    )
    run_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return run_id


def finish_sync_run(run_id: int, status: str, summary: dict | None = None, error_message: str | None = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE sync_runs
        SET status=?, finished_at=?, summary_json=?, error_message=?
        WHERE id=?
        """,
        (
            status,
            datetime.now().isoformat(timespec="seconds"),
            _json_dumps(summary or {}),
            error_message,
            run_id,
        ),
    )
    conn.commit()
    conn.close()


def save_raw_source_snapshot(
    trade_date: str,
    source_name: str,
    payload,
    *,
    sync_run_id: int | None = None,
    success: bool = True,
    error_message: str | None = None,
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO raw_source_snapshot
        (trade_date, sync_run_id, source_name, payload_json, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            trade_date,
            sync_run_id,
            source_name,
            _json_dumps(payload) if payload is not None else None,
            1 if success else 0,
            error_message,
        ),
    )
    conn.commit()
    conn.close()
    return data


REALTIME_SNAPSHOT_KEYS = (
    "turnover",
    "total_turnover",
    "concept_fund_flow",
    "concept_daily",
    "concept_quotes",
)


def _is_empty_snapshot_value(value) -> bool:
    return value in (None, "", [])


def _preserve_previous_when_empty(merged: dict, previous: dict, keys: tuple[str, ...]):
    for key in keys:
        if _is_empty_snapshot_value(merged.get(key)) and not _is_empty_snapshot_value(previous.get(key)):
            merged[key] = previous.get(key)


def _merge_market_statistics(
    current: dict,
    previous: dict,
    *,
    preserve_realtime_snapshot: bool,
) -> dict:
    stats = dict(current)
    keys = ("limit_up_count", "limit_down_count", "up_count", "down_count", "flat_count")
    for key in keys:
        previous_value = _number_or_none(previous.get(key))
        current_value = _number_or_none(stats.get(key))
        if current_value in (None, 0) and previous_value not in (None, 0):
            stats[key] = previous.get(key)

    if preserve_realtime_snapshot:
        for key in ("up_count", "down_count", "flat_count"):
            if previous.get(key) is not None:
                stats[key] = previous.get(key)

    return stats


def _merge_with_existing_report(data: dict, *, preserve_realtime_snapshot: bool = False) -> dict:
    trade_date = data.get("date")
    if not trade_date:
        return data

    existing = get_market_report(trade_date)
    if not existing:
        return data

    previous = existing.get("data") or {}
    if not isinstance(previous, dict):
        return data

    merged = dict(data)
    _preserve_previous_when_empty(
        merged,
        previous,
        (
            "turnover",
            "total_turnover",
            "indices",
            "index_data",
            "shanghai_index",
            "concept_fund_flow",
            "concept_daily",
            "concept_quotes",
            "stock_snapshot",
            "sectors",
            "sector_data",
            "sector_daily",
            "news",
        ),
    )
    if preserve_realtime_snapshot:
        for key in REALTIME_SNAPSHOT_KEYS:
            previous_value = previous.get(key)
            if previous_value not in (None, "", []):
                merged[key] = previous_value

    if (
        not _as_list(merged.get("limit_chain_stocks"))
        and _as_list(previous.get("limit_chain_stocks"))
    ):
        merged["market_statistics"] = previous.get("market_statistics")
        merged["turnover"] = previous.get("turnover")
        merged["total_turnover"] = previous.get("total_turnover")
        merged["indices"] = previous.get("indices")
        merged["index_data"] = previous.get("index_data")
        merged["shanghai_index"] = previous.get("shanghai_index")

    for key in ("limit_chain_stocks", "stock_snapshot", "sectors", "sector_data", "sector_daily", "news"):
        if not _as_list(merged.get(key)) and _as_list(previous.get(key)):
            merged[key] = previous.get(key)

    previous_stats = previous.get("market_statistics") or {}
    current_stats = merged.get("market_statistics") or {}
    if isinstance(previous_stats, dict) and isinstance(current_stats, dict):
        merged["market_statistics"] = _merge_market_statistics(
            current_stats,
            previous_stats,
            preserve_realtime_snapshot=preserve_realtime_snapshot,
        )

    return merged


def save_market_report(
    data: dict,
    markdown: str = "",
    sync_run_id: int | None = None,
    *,
    preserve_realtime_snapshot: bool = False,
):
    data = _merge_with_existing_report(
        data,
        preserve_realtime_snapshot=preserve_realtime_snapshot,
    )
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
            _json_dumps(data),
            markdown,
        ),
    )

    _save_raw_snapshots(cursor, data, sync_run_id)
    _save_index_daily(cursor, data)

    market_statistics = data.get("market_statistics") or {}
    if isinstance(market_statistics, dict):
        cursor.execute(
            """
            INSERT OR REPLACE INTO market_sentiment_daily
            (trade_date, up_count, down_count, limit_up_count, limit_down_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.get("date"),
                _number_or_none(market_statistics.get("up_count")),
                _number_or_none(market_statistics.get("down_count")),
                _number_or_none(market_statistics.get("limit_up_count")),
                _number_or_none(market_statistics.get("limit_down_count")),
            ),
        )

    sectors = _as_list(
        data.get("sectors") or data.get("sector_data") or data.get("sector_daily")
    )
    if sectors:
        cursor.execute("DELETE FROM sector_daily WHERE trade_date=?", (data.get("date"),))

    for sector in sectors:
        if not isinstance(sector, dict):
            continue

        sector_name = sector.get("sector_name") or sector.get("name")
        if not sector_name:
            continue

        cursor.execute(
            """
            INSERT INTO sector_daily
            (trade_date, sector_name, change_percent, limit_up_count, amount, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("date"),
                sector_name,
                _number_or_none(
                    sector.get("change_percent")
                    or sector.get("change")
                    or sector.get("value")
                ),
                _number_or_none(
                    sector.get("limit_up_count")
                    or sector.get("limitCount")
                    or sector.get("limit_count")
                ),
                _number_or_none(sector.get("amount") or sector.get("volume")),
                sector.get("source"),
            ),
        )

    margin_rows = _as_list(data.get("margin_balance"))
    for row in margin_rows:
        if not isinstance(row, dict):
            continue

        week_date = row.get("date") or row.get("week_date")
        margin_balance = row.get("margin_balance") or row.get("value")
        if not week_date:
            continue

        cursor.execute(
            """
            INSERT OR REPLACE INTO margin_balance_weekly
            (week_date, margin_balance)
            VALUES (?, ?)
            """,
            (
                week_date,
                _number_or_none(margin_balance),
            ),
        )

    _save_limit_up_daily(cursor, data)
    _save_stock_daily(cursor, data, preserve_realtime_snapshot=preserve_realtime_snapshot)
    _save_stock_snapshot_daily(cursor, data)
    _save_concept_daily(cursor, data)
    _save_news_daily(cursor, data)
    _save_plan2030_daily(cursor, data, preserve_realtime_snapshot=preserve_realtime_snapshot)

    conn.commit()
    conn.close()
    return data


def _save_raw_snapshots(cursor, data: dict, sync_run_id: int | None):
    trade_date = data.get("date")
    if not trade_date:
        return

    source_payloads = {
        "market_daily.normalized": data,
        "indices": data.get("indices") or data.get("index_data") or [],
        "market_statistics": data.get("market_statistics") or {},
        "limit_chain_stocks": data.get("limit_chain_stocks") or [],
        "stock_snapshot": data.get("stock_snapshot") or [],
        "sectors": data.get("sectors") or data.get("sector_data") or data.get("sector_daily") or [],
        "concept_fund_flow": data.get("concept_fund_flow") or data.get("concept_daily") or data.get("concept_quotes") or [],
        "margin_balance": data.get("margin_balance") or [],
        "news": data.get("news") or [],
    }
    for source_name, payload in source_payloads.items():
        cursor.execute(
            """
            INSERT INTO raw_source_snapshot
            (trade_date, sync_run_id, source_name, payload_json, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (trade_date, sync_run_id, source_name, _json_dumps(payload), 1, None),
        )

    for row in _as_list(data.get("source_errors")):
        if not isinstance(row, dict):
            continue
        cursor.execute(
            """
            INSERT INTO raw_source_snapshot
            (trade_date, sync_run_id, source_name, payload_json, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                trade_date,
                sync_run_id,
                _text_or_none(row.get("source")) or "unknown_source",
                None,
                0,
                _text_or_none(row.get("error")),
            ),
        )


def _save_index_daily(cursor, data: dict):
    trade_date = data.get("date")
    if not trade_date:
        return

    rows = _as_list(data.get("indices") or data.get("index_data"))
    if rows:
        cursor.execute("DELETE FROM index_daily WHERE trade_date=?", (trade_date,))

    for row in rows:
        if not isinstance(row, dict):
            continue
        index_name = _text_or_none(row.get("name") or row.get("index_name"))
        if not index_name:
            continue
        cursor.execute(
            """
            INSERT OR REPLACE INTO index_daily
            (
                trade_date, index_name, close, change_percent, open,
                high, low, amount, volume, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade_date,
                index_name,
                _number_or_none(row.get("close")),
                _number_or_none(_first_value(row, "change_pct", "change_percent", "change")),
                _number_or_none(row.get("open")),
                _number_or_none(row.get("high")),
                _number_or_none(row.get("low")),
                _number_or_none(row.get("amount")),
                _number_or_none(row.get("volume")),
                _text_or_none(row.get("source")),
            ),
        )


def _save_limit_up_daily(cursor, data: dict):
    trade_date = data.get("date")
    if not trade_date:
        return

    limit_rows = _as_list(data.get("limit_chain_stocks") or data.get("limit_up_stocks"))
    if limit_rows:
        cursor.execute("DELETE FROM limit_up_daily WHERE trade_date=?", (trade_date,))

    for row in limit_rows:
        if not isinstance(row, dict):
            continue
        stock_code = _text_or_none(row.get("stock_code") or row.get("code"))
        stock_name = _text_or_none(row.get("stock_name") or row.get("name"))
        if not stock_code or not stock_name:
            continue
        cursor.execute(
            """
            INSERT OR REPLACE INTO limit_up_daily
            (
                trade_date, stock_code, stock_name, industry, reason,
                change_percent, amount, free_float_market_cap, total_market_cap,
                turnover_rate, seal_amount, chain_days, detail, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade_date,
                stock_code,
                stock_name,
                _text_or_none(row.get("industry") or row.get("sector")),
                _text_or_none(row.get("reason") or row.get("concept") or row.get("industry")),
                _number_or_none(_first_value(row, "change_pct", "change_percent", "change")),
                _number_or_none(_first_value(row, "amount", "turnover")),
                _number_or_none(_first_value(row, "free_float_market_cap", "流通市值")),
                _number_or_none(_first_value(row, "total_market_cap", "总市值")),
                _number_or_none(_first_value(row, "turnover_rate", "换手率")),
                _number_or_none(_first_value(row, "seal_amount", "封板资金")),
                _number_or_none(row.get("chain_days") or row.get("board_count")),
                _text_or_none(row.get("detail") or row.get("sequence")),
                _text_or_none(row.get("source")) or "market_limit_up_pool",
            ),
        )


def _save_stock_daily(cursor, data: dict, *, preserve_realtime_snapshot: bool = False):
    trade_date = data.get("date")
    if not trade_date:
        return

    existing_by_code: dict[str, dict] = {}
    if preserve_realtime_snapshot:
        cursor.execute(
            """
            SELECT
                stock_code, amount, free_float_market_cap, total_market_cap,
                turnover_rate, seal_amount, main_net_inflow
            FROM stock_daily
            WHERE trade_date=?
            """,
            (trade_date,),
        )
        existing_by_code = {
            row[0]: {
                "amount": row[1],
                "free_float_market_cap": row[2],
                "total_market_cap": row[3],
                "turnover_rate": row[4],
                "seal_amount": row[5],
                "main_net_inflow": row[6],
            }
            for row in cursor.fetchall()
        }

    limit_rows = _as_list(data.get("limit_chain_stocks") or data.get("limit_up_stocks"))
    if limit_rows:
        cursor.execute("DELETE FROM stock_daily WHERE trade_date=? AND is_limit_up=1", (trade_date,))

    for row in limit_rows:
        if not isinstance(row, dict):
            continue

        stock_code = _text_or_none(row.get("stock_code") or row.get("code"))
        stock_name = _text_or_none(row.get("stock_name") or row.get("name"))
        if not stock_code or not stock_name:
            continue

        amount = _number_or_none(_first_value(row, "amount", "turnover"))
        free_float_market_cap = _number_or_none(_first_value(row, "free_float_market_cap", "流通市值"))
        total_market_cap = _number_or_none(_first_value(row, "total_market_cap", "总市值"))
        turnover_rate = _number_or_none(_first_value(row, "turnover_rate", "换手率"))
        seal_amount = _number_or_none(_first_value(row, "seal_amount", "封板资金"))
        main_net_inflow = _number_or_none(_first_value(row, "main_net_inflow", "inflow"))
        existing = existing_by_code.get(stock_code, {})
        if preserve_realtime_snapshot:
            if amount is None and existing.get("amount") is not None:
                amount = existing["amount"]
            if free_float_market_cap is None and existing.get("free_float_market_cap") is not None:
                free_float_market_cap = existing["free_float_market_cap"]
            if total_market_cap is None and existing.get("total_market_cap") is not None:
                total_market_cap = existing["total_market_cap"]
            if turnover_rate is None and existing.get("turnover_rate") is not None:
                turnover_rate = existing["turnover_rate"]
            if seal_amount is None and existing.get("seal_amount") is not None:
                seal_amount = existing["seal_amount"]
            if main_net_inflow is None and existing.get("main_net_inflow") is not None:
                main_net_inflow = existing["main_net_inflow"]

        cursor.execute(
            """
            INSERT OR REPLACE INTO stock_daily
            (
                trade_date, stock_code, stock_name, industry, role,
                change_percent, amount, free_float_market_cap, total_market_cap,
                turnover_rate, seal_amount, main_net_inflow, is_limit_up,
                chain_days, detail, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade_date,
                stock_code,
                stock_name,
                _text_or_none(row.get("industry") or row.get("sector")),
                _text_or_none(row.get("reason") or row.get("concept") or row.get("industry")),
                _number_or_none(_first_value(row, "change_pct", "change_percent", "change")),
                amount,
                free_float_market_cap,
                total_market_cap,
                turnover_rate,
                seal_amount,
                main_net_inflow,
                1,
                _number_or_none(row.get("chain_days") or row.get("board_count")),
                _text_or_none(row.get("detail") or row.get("sequence")),
                _text_or_none(row.get("source")) or "market_limit_up_pool",
            ),
        )


def _save_stock_snapshot_daily(cursor, data: dict):
    trade_date = data.get("date")
    if not trade_date:
        return

    rows = _as_list(data.get("stock_snapshot"))
    if rows:
        cursor.execute("DELETE FROM stock_snapshot_daily WHERE trade_date=?", (trade_date,))

    for row in rows:
        if not isinstance(row, dict):
            continue
        stock_code = _text_or_none(row.get("stock_code") or row.get("code"))
        stock_name = _text_or_none(row.get("stock_name") or row.get("name"))
        if not stock_code or not stock_name:
            continue

        cursor.execute(
            """
            INSERT OR REPLACE INTO stock_snapshot_daily
            (
                trade_date, stock_code, stock_name, close, change_percent,
                amount, free_float_market_cap, total_market_cap, turnover_rate, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade_date,
                stock_code,
                stock_name,
                _number_or_none(_first_value(row, "close", "最新价")),
                _number_or_none(_first_value(row, "change_pct", "change_percent", "涨跌幅")),
                _number_or_none(_first_value(row, "amount", "成交额")),
                _number_or_none(_first_value(row, "free_float_market_cap", "流通市值")),
                _number_or_none(_first_value(row, "total_market_cap", "总市值")),
                _number_or_none(_first_value(row, "turnover_rate", "换手率")),
                _text_or_none(row.get("source")) or "akshare.stock_zh_a_spot_em",
            ),
        )


def _concept_name(row: dict) -> str | None:
    return _text_or_none(_first_value(row, "concept_name", "sector_name", "板块名称", "名称", "行业", "概念名称", "name"))


def _concept_change(row: dict) -> float | None:
    return _number_or_none(_first_value(row, "change_percent", "change", "涨跌幅", "涨跌幅%", "今日涨跌幅", "行业-涨跌幅", "涨幅"))


def _concept_amount(row: dict) -> float | None:
    value = _number_or_none(_first_value(row, "amount", "turnover", "成交额", "成交额(元)", "今日成交额"))
    if value is not None and abs(value) > 1_000_000:
        return value / 100_000_000
    inflow = _number_or_none(_first_value(row, "流入资金"))
    outflow = _number_or_none(_first_value(row, "流出资金"))
    if inflow is not None and outflow is not None:
        return round(inflow + outflow, 2)
    return value


def _net_inflow(row: dict) -> float | None:
    value = _number_or_none(
        _first_value(
            row,
            "main_net_inflow",
            "inflow",
            "净额",
            "主力净流入-净额",
            "今日主力净流入-净额",
            "今日主力净流入净额",
            "主力净流入",
            "净流入",
        )
    )
    return value / 100_000_000 if value and abs(value) > 1_000_000 else value


def _save_concept_daily(cursor, data: dict):
    trade_date = data.get("date")
    if not trade_date:
        return

    rows = _as_list(data.get("concept_daily") or data.get("concept_fund_flow") or data.get("concept_quotes"))
    if rows:
        cursor.execute("DELETE FROM concept_daily WHERE trade_date=?", (trade_date,))

    for row in rows:
        if not isinstance(row, dict):
            continue

        concept_name = _concept_name(row)
        if not concept_name:
            continue

        cursor.execute(
            """
            INSERT OR REPLACE INTO concept_daily
            (
                trade_date, concept_name, change_percent, amount, main_net_inflow,
                leader_code, leader_name, leader_change_percent, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade_date,
                concept_name,
                _concept_change(row),
                _concept_amount(row),
                _net_inflow(row),
                _text_or_none(_first_value(row, "leader_code", "领涨股代码")),
                _text_or_none(_first_value(row, "leader_name", "领涨股", "leader")),
                _number_or_none(_first_value(row, "leader_change_percent", "领涨股-涨跌幅")),
                _text_or_none(row.get("source")) or "market_concept_flow",
            ),
        )


def _save_news_daily(cursor, data: dict):
    trade_date = data.get("date")
    if not trade_date:
        return

    rows = _as_list(data.get("news"))
    if rows:
        cursor.execute("DELETE FROM news_daily WHERE trade_date=?", (trade_date,))

    for row in rows:
        if not isinstance(row, dict):
            continue
        title = _text_or_none(row.get("title") or row.get("headline"))
        if not title:
            continue
        cursor.execute(
            """
            INSERT INTO news_daily
            (trade_date, title, category, event_time, url, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                trade_date,
                title,
                _text_or_none(row.get("category")),
                _text_or_none(row.get("time") or row.get("date")),
                _text_or_none(row.get("url")),
                _text_or_none(row.get("source")),
            ),
        )


def _save_plan2030_daily(cursor, data: dict, *, preserve_realtime_snapshot: bool = False):
    trade_date = data.get("date")
    themes = _load_plan_themes()
    if not trade_date or not themes:
        return

    existing_theme_by_id: dict[str, dict] = {}
    existing_theme_stock_by_key: dict[tuple[str, str], dict] = {}
    if preserve_realtime_snapshot:
        cursor.execute(
            """
            SELECT theme_id, amount, main_net_inflow
            FROM plan_theme_daily
            WHERE trade_date=?
            """,
            (trade_date,),
        )
        existing_theme_by_id = {
            row[0]: {"amount": row[1], "main_net_inflow": row[2]}
            for row in cursor.fetchall()
        }
        cursor.execute(
            """
            SELECT theme_id, stock_code, main_net_inflow
            FROM plan_theme_stock_daily
            WHERE trade_date=?
            """,
            (trade_date,),
        )
        existing_theme_stock_by_key = {
            (row[0], row[1]): {"main_net_inflow": row[2]}
            for row in cursor.fetchall()
        }

    stock_rows = [
        row
        for row in _as_list(data.get("limit_chain_stocks") or data.get("limit_up_stocks"))
        if isinstance(row, dict)
    ]
    concept_rows = [
        row
        for row in _as_list(data.get("concept_daily") or data.get("concept_fund_flow") or data.get("concept_quotes"))
        if isinstance(row, dict)
    ]
    news_rows = [row for row in _as_list(data.get("news")) if isinstance(row, dict)]

    cursor.execute("DELETE FROM plan_theme_daily WHERE trade_date=?", (trade_date,))
    cursor.execute("DELETE FROM plan_theme_stock_daily WHERE trade_date=?", (trade_date,))

    for theme in themes:
        keywords = [str(item) for item in theme.get("keywords", [])]
        matched_stocks = [
            row
            for row in stock_rows
            if _contains_keyword(row, keywords, ("stock_name", "name", "industry", "reason", "concept", "sector"))
        ]
        matched_concepts = [
            row
            for row in concept_rows
            if _contains_keyword(row, keywords, ("concept_name", "sector_name", "板块名称", "名称", "行业", "概念名称", "name"))
        ]
        matched_news = [
            row
            for row in news_rows
            if _contains_keyword(row, keywords, ("title", "headline", "category"))
        ]

        concept_change = _average([_concept_change(row) for row in matched_concepts])
        concept_amount = _sum_or_none([_concept_amount(row) for row in matched_concepts])
        concept_inflow = _sum_or_none([_net_inflow(row) for row in matched_concepts])
        existing_theme = existing_theme_by_id.get(str(theme.get("id")), {})
        if preserve_realtime_snapshot:
            if concept_amount is None and existing_theme.get("amount") is not None:
                concept_amount = existing_theme["amount"]
            if concept_inflow is None and existing_theme.get("main_net_inflow") is not None:
                concept_inflow = existing_theme["main_net_inflow"]
        limit_up_count = len(matched_stocks)
        leader_count = min(limit_up_count, 5)
        score = min(
            100,
            limit_up_count * 8
            + len(matched_concepts) * 6
            + min(len(matched_news), 3) * 6
            + leader_count * 3
            + max(0, int((concept_change or 0) * 4))
            + max(0, int((concept_inflow or 0) / 2)),
        )
        status = _plan_status(score, limit_up_count, concept_inflow)

        cursor.execute(
            """
            INSERT OR REPLACE INTO plan_theme_daily
            (
                trade_date, theme_id, theme_name, axis, score, status,
                change_percent, amount, main_net_inflow,
                limit_up_count, leader_count, catalyst_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade_date,
                theme.get("id"),
                theme.get("name"),
                theme.get("axis"),
                score,
                status,
                concept_change,
                concept_amount,
                concept_inflow,
                limit_up_count,
                leader_count,
                min(len(matched_news), 3),
            ),
        )

        for row in matched_stocks[:5]:
            stock_code = _text_or_none(row.get("stock_code") or row.get("code"))
            stock_name = _text_or_none(row.get("stock_name") or row.get("name"))
            if not stock_code or not stock_name:
                continue
            stock_inflow = _number_or_none(_first_value(row, "main_net_inflow", "inflow"))
            existing_stock = existing_theme_stock_by_key.get((str(theme.get("id")), stock_code), {})
            if (
                preserve_realtime_snapshot
                and stock_inflow is None
                and existing_stock.get("main_net_inflow") is not None
            ):
                stock_inflow = existing_stock["main_net_inflow"]
            cursor.execute(
                """
                INSERT OR REPLACE INTO plan_theme_stock_daily
                (
                    trade_date, theme_id, stock_code, stock_name, role,
                    change_percent, main_net_inflow, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade_date,
                    theme.get("id"),
                    stock_code,
                    stock_name,
                    _text_or_none(row.get("industry") or row.get("reason") or "主题映射"),
                    _number_or_none(_first_value(row, "change_pct", "change_percent", "change")),
                    stock_inflow,
                    _text_or_none(row.get("source")) or "market_limit_up_pool",
                ),
            )


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


def get_latest_market_report():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT trade_date, json_content, markdown_content
        FROM market_reports
        ORDER BY trade_date DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "date": row[0],
        "data": json.loads(row[1]),
        "markdown": row[2],
    }


def get_recent_market_reports(limit: int = 30):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT trade_date, json_content, markdown_content
        FROM market_reports
        ORDER BY trade_date DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "date": row[0],
            "data": json.loads(row[1]),
            "markdown": row[2],
        }
        for row in rows
    ]


def get_latest_sync_run(trade_date: str | None = None):
    conn = get_connection()
    cursor = conn.cursor()
    if trade_date:
        cursor.execute(
            """
            SELECT id, trade_date, status, started_at, finished_at, summary_json, error_message
            FROM sync_runs
            WHERE trade_date=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (trade_date,),
        )
    else:
        cursor.execute(
            """
            SELECT id, trade_date, status, started_at, finished_at, summary_json, error_message
            FROM sync_runs
            ORDER BY id DESC
            LIMIT 1
            """
        )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "date": row[1],
        "status": row[2],
        "startedAt": row[3],
        "finishedAt": row[4],
        "summary": json.loads(row[5]) if row[5] else {},
        "error": row[6],
    }


def get_raw_source_snapshots(trade_date: str, limit: int = 50) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, trade_date, sync_run_id, source_name, success, error_message, created_at
        FROM raw_source_snapshot
        WHERE trade_date=?
        ORDER BY id DESC
        LIMIT ?
        """,
        (trade_date, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "date": row[1],
            "syncRunId": row[2],
            "source": row[3],
            "success": bool(row[4]),
            "error": row[5],
            "createdAt": row[6],
        }
        for row in rows
    ]


def get_stock_daily(trade_date: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            trade_date, stock_code, stock_name, industry, role,
            change_percent, amount, free_float_market_cap, total_market_cap,
            turnover_rate, seal_amount, main_net_inflow, is_limit_up,
            chain_days, detail, source
        FROM stock_daily
        WHERE trade_date=?
        ORDER BY is_limit_up DESC, chain_days DESC, stock_code
        """,
        (trade_date,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "date": row[0],
            "code": row[1],
            "name": row[2],
            "industry": row[3],
            "role": row[4],
            "change": row[5],
            "amount": row[6],
            "freeFloatMarketCap": row[7],
            "totalMarketCap": row[8],
            "turnoverRate": row[9],
            "sealAmount": row[10],
            "inflow": row[11],
            "isLimitUp": bool(row[12]),
            "chainDays": row[13],
            "detail": row[14],
            "source": row[15],
        }
        for row in rows
    ]


def get_stock_snapshot_daily(trade_date: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            trade_date, stock_code, stock_name, close, change_percent,
            amount, free_float_market_cap, total_market_cap, turnover_rate, source
        FROM stock_snapshot_daily
        WHERE trade_date=?
        ORDER BY free_float_market_cap DESC, total_market_cap DESC, stock_code
        """,
        (trade_date,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "date": row[0],
            "code": row[1],
            "name": row[2],
            "close": row[3],
            "change": row[4],
            "amount": row[5],
            "freeFloatMarketCap": row[6],
            "totalMarketCap": row[7],
            "turnoverRate": row[8],
            "source": row[9],
        }
        for row in rows
    ]


def get_concept_daily(trade_date: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            trade_date, concept_name, change_percent, amount, main_net_inflow,
            leader_code, leader_name, leader_change_percent, source
        FROM concept_daily
        WHERE trade_date=?
        ORDER BY main_net_inflow DESC, change_percent DESC
        """,
        (trade_date,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "date": row[0],
            "name": row[1],
            "change": row[2],
            "amount": row[3],
            "inflow": row[4],
            "leaderCode": row[5],
            "leaderName": row[6],
            "leaderChange": row[7],
            "source": row[8],
        }
        for row in rows
    ]


def get_plan2030_theme_daily(trade_date: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            trade_date, theme_id, theme_name, axis, score, status,
            change_percent, amount, main_net_inflow,
            limit_up_count, leader_count, catalyst_count
        FROM plan_theme_daily
        WHERE trade_date=?
        ORDER BY score DESC, limit_up_count DESC, theme_id
        """,
        (trade_date,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "date": row[0],
            "id": row[1],
            "name": row[2],
            "axis": row[3],
            "score": row[4],
            "status": row[5],
            "change": row[6],
            "turnover": row[7],
            "inflow": row[8],
            "limitUp": row[9],
            "leaderCount": row[10],
            "catalystCount": row[11],
        }
        for row in rows
    ]


def get_plan2030_theme_stocks(trade_date: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            trade_date, theme_id, stock_code, stock_name, role,
            change_percent, main_net_inflow, source
        FROM plan_theme_stock_daily
        WHERE trade_date=?
        ORDER BY theme_id, main_net_inflow DESC, change_percent DESC, stock_code
        """,
        (trade_date,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "date": row[0],
            "themeId": row[1],
            "code": row[2],
            "name": row[3],
            "role": row[4],
            "change": row[5],
            "inflow": row[6],
            "source": row[7],
        }
        for row in rows
    ]
