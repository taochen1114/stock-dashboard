from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# 美股追蹤清單
US_STOCKS = {
    "AMZN": "亞馬遜 (AWS)",
    "GOOGL": "Google",
    "META": "Meta",
    "MSFT": "微軟",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "AAPL": "Apple",
    "TSM": "台積電 ADR",
    "VOO": "Vanguard S&P500 ETF",
    "VT": "Vanguard 全球 ETF",
    "VTI": "Vanguard 美國全市場 ETF",
    "SSO": "2x S&P500 ETF",
    "SPY": "S&P 500 ETF",
}

# 台股追蹤清單（yfinance 格式加 .TW）
TW_STOCKS = {
    "2330.TW": "台積電",
    "2454.TW": "聯發科",
    "2308.TW": "台達電",
    "2317.TW": "鴻海",
    "0050.TW": "元大台灣50",
    "0056.TW": "元大高股息",
    "00878.TW": "國泰永續高股息",
    "006208.TW": "富邦台50",
    "2882.TW": "國泰金控",
    "2892.TW": "第一金",
    "2891.TW": "中信金",
    "2881.TW": "富邦金",
    "2884.TW": "玉山金",
}

# 時間維度對應 yfinance period 參數
PERIOD_MAP = {
    "1w": "5d",
    "1m": "1mo",
    "3m": "3mo",
    "6m": "6mo",
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
}

# 新聞 RSS 來源
NEWS_FEEDS = [
    "https://finance.yahoo.com/news/rssindex",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^TWII&region=US&lang=en-US",
    "https://news.google.com/rss/search?q=台股+股市&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=US+stock+market&hl=en-US&gl=US&ceid=US:en",
]
