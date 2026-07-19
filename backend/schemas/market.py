"""AIMS market data schemas.

Pydantic models define the contract between AI collectors and storage.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class IndexData(BaseModel):
    name: Optional[str] = None
    index_name: Optional[str] = None
    date: Optional[str] = None
    close: Optional[float] = None
    change_pct: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    amount: Optional[float] = None
    volume: Optional[float] = None
    source: Optional[str] = None


class MarketStatistics(BaseModel):
    up_count: Optional[int] = None
    down_count: Optional[int] = None
    flat_count: Optional[int] = None
    limit_up_count: Optional[int] = None
    limit_down_count: Optional[int] = None


class SectorData(BaseModel):
    rank: Optional[int] = None
    sector_name: str
    name: Optional[str] = None
    limit_up_count: Optional[int] = None
    change_percent: Optional[float] = None
    amount: Optional[float] = None
    source: Optional[str] = None


class LimitChainStock(BaseModel):
    stock_code: str
    stock_name: str
    chain_days: Optional[int] = None
    detail: Optional[str] = None
    industry: Optional[str] = None
    reason: Optional[str] = None


class MarginBalance(BaseModel):
    date: str
    margin_balance: Optional[float] = None
    source: Optional[str] = None


class NewsEvent(BaseModel):
    time: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None
    title: Optional[str] = None
    headline: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None


class MarketDailySchema(BaseModel):
    schema_version: str = "1.0"
    date: str
    turnover: Optional[float] = None
    total_turnover: Optional[float] = None
    shanghai_index: Optional[IndexData] = None
    indices: List[IndexData] = Field(default_factory=list)
    index_data: List[IndexData] = Field(default_factory=list)
    market_statistics: Optional[MarketStatistics] = None
    limit_chain_stocks: List[LimitChainStock] = Field(default_factory=list)
    sectors: List[SectorData] = Field(default_factory=list)
    margin_balance: List[MarginBalance] = Field(default_factory=list)
    news: List[NewsEvent] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    source_errors: List[dict] = Field(default_factory=list)
