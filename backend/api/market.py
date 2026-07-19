"""Market data API endpoints."""

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.run_akshare_collector import build_summary, collect_market_data
from backend.api.market_service import query_latest_market, query_market_by_date
from backend.services.trade_calendar import is_trade_day

router = APIRouter(prefix="/api/market", tags=["market"])


class MarketSyncRequest(BaseModel):
    trade_date: date


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/latest")
def get_latest_market():
    """Get the latest stored market data."""
    result = query_latest_market()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="market data not found",
        )

    return result


@router.post("/sync")
def sync_market(request: MarketSyncRequest):
    """Collect and persist market data for the requested trade date."""
    trade_date = request.trade_date.isoformat()
    if not is_trade_day(trade_date):
        return {
            "ok": False,
            "date": trade_date,
            "reason": "non_trading_day",
            "message": f"{trade_date} 非 A 股交易日，无需同步",
        }

    try:
        data = collect_market_data(trade_date)
    except Exception as exc:  # noqa: BLE001 - expose a concise API error.
        raise HTTPException(
            status_code=500,
            detail=f"market sync failed: {type(exc).__name__}: {exc}",
        ) from exc

    return {
        "ok": True,
        "date": trade_date,
        "summary": build_summary(data),
    }


@router.get("/{trade_date}")
def get_market(trade_date: date):
    """Get stored market data by trade date."""
    result = query_market_by_date(trade_date.isoformat())

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="market data not found",
        )

    return result
