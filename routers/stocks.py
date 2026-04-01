from fastapi import APIRouter, HTTPException
from services.stock_service import fetch_all_quotes, fetch_quote, fetch_history
from config import US_STOCKS, TW_STOCKS

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

ALL_STOCKS = {**US_STOCKS, **TW_STOCKS}


@router.get("/latest")
def get_all_latest():
    """取得所有股票最新報價"""
    return fetch_all_quotes()


@router.get("/{symbol:path}/latest")
def get_stock_latest(symbol: str):
    """取得單一股票最新報價"""
    quote = fetch_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"無法取得 {symbol} 的資料")
    return quote


@router.get("/{symbol:path}/history")
def get_stock_history(symbol: str, period: str = "1m"):
    """
    取得股票歷史資料
    period: 1w | 1m | 3m | 6m | 1y | 2y | 5y
    """
    valid_periods = ["1w", "1m", "3m", "6m", "1y", "2y", "5y"]
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"period 需為 {valid_periods} 其中之一")

    history = fetch_history(symbol, period)
    if not history:
        raise HTTPException(status_code=404, detail=f"無法取得 {symbol} 的歷史資料")
    return history


@router.get("/list/all")
def get_stock_list():
    """取得所有追蹤的股票清單"""
    us = [{"symbol": k, "name": v, "market": "US"} for k, v in US_STOCKS.items()]
    tw = [{"symbol": k, "name": v, "market": "TW"} for k, v in TW_STOCKS.items()]
    return {"US": us, "TW": tw}
