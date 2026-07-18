"""AIMS market data schemas.

Pydantic models define the contract between AI collectors and storage.
"""

from typing import Optional, List
from pydantic import BaseModel


class IndexData(BaseModel):
    close: Optional[float] = None
    change_pct: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    amount: Optional[float] = None
    source: Optional[str] = None


class MarketStatistics(BaseModel):
    up_count: Optional[int] = None
    down_count: Optional[int] = None
    flat_count: Optional[int] = None
    limit_up_count: Optional[int] = None
    limit_down_count: Optional[int] = None


class MarketDailySchema(BaseModel):
    schema_version: str = "1.0"
    date: str
    shanghai_index: Optional[IndexData] = None
    market_statistics: Optional[MarketStatistics] = None
    sources: List[str] = []
