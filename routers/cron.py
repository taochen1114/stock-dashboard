from fastapi import APIRouter, Header, HTTPException
from datetime import date
from config import REFRESH_API_KEY
from database import SessionLocal, DailyReport as DailyReportModel
from services.stock_service import fetch_all_quotes
from services.news_service import fetch_news
from services.ai_service import generate_daily_report

router = APIRouter(prefix="/api/cron", tags=["cron"])


def verify_key(x_api_key: str = Header(default="")):
    if REFRESH_API_KEY and x_api_key != REFRESH_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("/warmup")
def warmup(x_api_key: str = Header(default="")):
    """喚醒 Render 並預熱股票快取"""
    verify_key(x_api_key)
    quotes = fetch_all_quotes()
    us_count = len(quotes.get("US", []))
    tw_count = len(quotes.get("TW", []))
    return {"status": "ok", "us": us_count, "tw": tw_count}


@router.post("/daily-report")
def trigger_daily_report(x_api_key: str = Header(default="")):
    """強制生成今日分析報告（若已存在則覆蓋）"""
    verify_key(x_api_key)
    today = str(date.today())
    db = SessionLocal()
    try:
        existing = db.query(DailyReportModel).filter(DailyReportModel.date == today).first()
        if existing:
            db.delete(existing)
            db.commit()

        quotes = fetch_all_quotes()
        news = fetch_news(limit=15)
        content = generate_daily_report(
            us_stocks=quotes.get("US", []),
            tw_stocks=quotes.get("TW", []),
            news=news,
        )
        record = DailyReportModel(date=today, content=content)
        db.add(record)
        db.commit()
        return {"status": "ok", "date": today, "length": len(content)}
    finally:
        db.close()
