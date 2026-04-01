import yfinance as yf
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from config import US_STOCKS, TW_STOCKS, PERIOD_MAP
from models.schemas import StockQuote, StockHistory, HistoryPoint


ALL_STOCKS = {**US_STOCKS, **{k: v for k, v in TW_STOCKS.items()}}

# 記憶體快取：避免頻繁重複抓取
_quote_cache: dict = {}
_cache_lock = Lock()
_cache_ttl_minutes = 10  # 快取 10 分鐘


def get_market(symbol: str) -> str:
    return "TW" if symbol.endswith(".TW") else "US"


def _is_cache_valid(symbol: str) -> bool:
    with _cache_lock:
        if symbol not in _quote_cache:
            return False
        cached_at = _quote_cache[symbol]["cached_at"]
        return datetime.now() - cached_at < timedelta(minutes=_cache_ttl_minutes)


def fetch_quote(symbol: str) -> StockQuote | None:
    if _is_cache_valid(symbol):
        return _quote_cache[symbol]["data"]

    try:
        ticker = yf.Ticker(symbol)

        # fast_info 提供最即時報價（含盤中），history 提供 OHLCV
        fi = ticker.fast_info
        hist = ticker.history(period="5d")
        hist = hist.dropna(subset=["Close"])

        if hist.empty:
            return None

        # 最即時價格：優先用 fast_info.last_price，fallback 用 history 最後收盤
        last_price = getattr(fi, "last_price", None)
        price = float(last_price) if last_price else float(hist.iloc[-1]["Close"])

        # 前一交易日收盤（用來算漲跌幅）
        prev_close_raw = getattr(fi, "previous_close", None)
        if prev_close_raw:
            prev_close = float(prev_close_raw)
        elif len(hist) >= 2:
            prev_close = float(hist.iloc[-2]["Close"])
        else:
            prev_close = price

        change = price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        # 今日 OHLCV 來自 history 最後一列
        latest = hist.iloc[-1]
        last_volume = getattr(fi, "last_volume", None)
        volume = float(last_volume) if last_volume else float(latest["Volume"])

        name = ALL_STOCKS.get(symbol, symbol)
        market = get_market(symbol)

        quote = StockQuote(
            symbol=symbol,
            name=name,
            market=market,
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
        with _cache_lock:
            _quote_cache[symbol] = {"data": quote, "cached_at": datetime.now()}
        return quote
    except Exception as e:
        print(f"[stock_service] fetch_quote error for {symbol}: {e}")
        return None


def fetch_all_quotes() -> dict:
    results = {"US": [], "TW": []}
    all_symbols = list(US_STOCKS.keys()) + list(TW_STOCKS.keys())

    # 平行抓取，最多 10 個 thread 同時執行
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
        hist = hist.dropna(subset=["Open", "High", "Low", "Close"])  # 過濾所有 NaN 列

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
                volume=float(row["Volume"]) if not __import__("math").isnan(row["Volume"]) else 0.0,
            ))

        name = ALL_STOCKS.get(symbol, symbol)
        market = get_market(symbol)

        return StockHistory(
            symbol=symbol,
            name=name,
            market=market,
            period=period,
            data=data,
        )
    except Exception as e:
        print(f"[stock_service] fetch_history error for {symbol}: {e}")
        return None
