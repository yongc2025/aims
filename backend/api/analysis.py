"""Analysis API endpoints for charts and dashboards."""

from fastapi import APIRouter, Query

from backend.services.margin_service import get_margin_trend
from backend.services.sentiment_service import get_sentiment_trend
from backend.services.sector_service import get_sector_heatmap

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/margin")
def margin(date: str | None = Query(default=None)):
    return get_margin_trend(date)


@router.get("/sentiment")
def sentiment(date: str | None = Query(default=None)):
    return get_sentiment_trend(date)


@router.get("/sectors")
def sectors(date: str | None = Query(default=None)):
    return get_sector_heatmap(date)
