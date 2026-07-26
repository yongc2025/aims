"""Fifteenth Five-Year Plan theme radar API."""

from fastapi import APIRouter

from backend.services.plan2030_service import get_plan2030_daily

router = APIRouter(prefix="/api/plan2030", tags=["plan2030"])


@router.get("/daily")
def daily():
    """Return policy theme radar data for the latest stored report."""
    return get_plan2030_daily()
