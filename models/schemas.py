from pydantic import BaseModel
from typing import Optional, List


class StockQuote(BaseModel):
    symbol: str
    name: str
    market: str  # "US" or "TW"
    price: float
    open: float
    high: float
    low: float
    close: float
    prev_close: float
    change: float
    change_pct: float
    volume: float
    date: str


class HistoryPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class StockHistory(BaseModel):
    symbol: str
    name: str
    market: str
    period: str
    data: List[HistoryPoint]


class DailyReport(BaseModel):
    date: str
    content: str


class NewsItem(BaseModel):
    title: str
    link: str
    published: Optional[str] = None
    source: Optional[str] = None
