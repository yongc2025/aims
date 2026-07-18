"""Analysis API endpoints for charts and dashboards."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/margin")
def get_margin_trend():
    return []


@router.get("/sentiment")
def get_sentiment_trend():
    return []


@router.get("/sectors")
def get_sector_heatmap():
    return []
