"""Analysis API endpoints for charts and dashboards."""

from fastapi import APIRouter

from backend.services.margin_service import get_margin_trend
from backend.services.sentiment_service import get_sentiment_trend
from backend.services.sector_service import get_sector_heatmap

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/margin")
def margin():
    return get_margin_trend()


@router.get("/sentiment")
def sentiment():
    return get_sentiment_trend()


@router.get("/sectors")
def sectors():
    return get_sector_heatmap()
