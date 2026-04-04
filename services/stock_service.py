import math
import yfinance as yf
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from config import US_STOCKS, TW_STOCKS, PERIOD_MAP
from models.schemas import StockQuote, StockHistory, HistoryPoint
from database import SessionLocal, StockPrice as StockPriceModel


ALL_STOCKS = {**US_STOCKS, **{k: v for k, v in TW_STOCKS.items()}}

# 記憶體快取
_quote_cache: dict = {}
_cache_lock = Lock()
_cache_ttl_minutes = 10  # 記憶體快取 10 分鐘
_db_cache_ttl_minutes = 60  # DB 快取 60 分鐘（服務重啟後仍有效）


def get_market(symbol: str) -> str:
    return "TW" if symbol.endswith(".TW") else "US"


def _is_memory_cache_valid(symbol: str) -> bool:
    with _cache_lock:
        if symbol not in _quote_cache:
            return False
        return datetime.now() - _quote_cache[symbol]["cached_at"] < timedelta(minutes=_cache_ttl_minutes)


def _load_from_db(symbol: str) -> StockQuote | None:
    """從 SQLite 讀取最近的快取（服務重啟後的 fallback）"""
    db = SessionLocal()
    try:
        row = (
            db.query(StockPriceModel)
            .filter(StockPriceModel.symbol == symbol)
            .order_by(StockPriceModel.created_at.desc())
            .first()
        )
        if not row:
            return None
        # 超過 60 分鐘的 DB 快取視為過期
        if datetime.utcnow() - row.created_at > timedelta(minutes=_db_cache_ttl_minutes):
            return None
        return StockQuote(
            symbol=row.symbol,
            name=ALL_STOCKS.get(row.symbol, row.symbol),
            market=row.market,
            price=row.close,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            prev_close=row.close,  # DB 快取不存 prev_close，用 close 代替
            change=0.0,
            change_pct=0.0,
            volume=row.volume,
            date=row.date,
        )
    finally:
        db.close()


def _save_to_db(quote: StockQuote):
    """把最新報價存進 SQLite"""
    db = SessionLocal()
    try:
        # 刪除同 symbol 舊紀錄，只保留最新一筆
        db.query(StockPriceModel).filter(StockPriceModel.symbol == quote.symbol).delete()
        row = StockPriceModel(
            symbol=quote.symbol,
            date=quote.date,
            open=quote.open,
            high=quote.high,
            low=quote.low,
            close=quote.price,
            volume=quote.volume,
            market=quote.market,
        )
        db.add(row)
        db.commit()
    except Exception as e:
        print(f"[stock_service] _save_to_db error for {quote.symbol}: {e}")
    finally:
        db.close()


def fetch_quote(symbol: str) -> StockQuote | None:
    # 1. 記憶體快取
    if _is_memory_cache_valid(symbol):
        return _quote_cache[symbol]["data"]

    # 2. DB 快取（服務重啟後的 fallback）
    db_quote = _load_from_db(symbol)

    try:
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info
        hist = ticker.history(period="5d")
        hist = hist.dropna(subset=["Close"])

        if hist.empty:
            return db_quote  # yfinance 失敗時回傳 DB 快取

        last_price = getattr(fi, "last_price", None)
        price = float(last_price) if last_price else float(hist.iloc[-1]["Close"])

        prev_close_raw = getattr(fi, "previous_close", None)
        if prev_close_raw:
            prev_close = float(prev_close_raw)
        elif len(hist) >= 2:
            prev_close = float(hist.iloc[-2]["Close"])
        else:
            prev_close = price

        change = price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        latest = hist.iloc[-1]
        last_volume = getattr(fi, "last_volume", None)
        volume = float(last_volume) if last_volume else float(latest["Volume"])

        quote = StockQuote(
            symbol=symbol,
            name=ALL_STOCKS.get(symbol, symbol),
            market=get_market(symbol),
            price=round(price, 2),
            open=round(float(latest["Open"]), 2),
            high=round(float(latest["High"]), 2),
            low=round(float(latest["Low"]), 2),
            close=round(price, 2),
            prev_close=round(prev_close, 2),
            change=round(change, 2),
            change_pct=round(change_pct, 2),
            volume=volume,
            date=str(hist.index[-1].date()),
        )

        # 同時寫入記憶體快取 & DB
        with _cache_lock:
            _quote_cache[symbol] = {"data": quote, "cached_at": datetime.now()}
        _save_to_db(quote)
        return quote

    except Exception as e:
        print(f"[stock_service] fetch_quote error for {symbol}: {e}")
        return db_quote  # yfinance 失敗時回傳 DB 快取


def fetch_all_quotes() -> dict:
    results = {"US": [], "TW": []}
    all_symbols = list(US_STOCKS.keys()) + list(TW_STOCKS.keys())

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_quote, symbol): symbol for symbol in all_symbols}
        for future in as_completed(futures):
            quote = future.result()
            if quote:
                results[quote.market].append(quote)

    return results


def fetch_history(symbol: str, period: str) -> StockHistory | None:
    try:
        yf_period = PERIOD_MAP.get(period, "1mo")
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=yf_period)
        hist = hist.dropna(subset=["Open", "High", "Low", "Close"])

        if hist.empty:
            return None

        data = []
        for idx, row in hist.iterrows():
            data.append(HistoryPoint(
                date=str(idx.date()),
                open=round(float(row["Open"]), 2),
                high=round(float(row["High"]), 2),
                low=round(float(row["Low"]), 2),
                close=round(float(row["Close"]), 2),
                volume=float(row["Volume"]) if not math.isnan(row["Volume"]) else 0.0,
            ))

        return StockHistory(
            symbol=symbol,
            name=ALL_STOCKS.get(symbol, symbol),
            market=get_market(symbol),
            period=period,
            data=data,
        )
    except Exception as e:
        print(f"[stock_service] fetch_history error for {symbol}: {e}")
        return None
