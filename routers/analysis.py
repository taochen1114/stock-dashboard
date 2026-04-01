from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from database import get_db, DailyReport as DailyReportModel
from services.stock_service import fetch_all_quotes
from services.news_service import fetch_news
from services.ai_service import generate_daily_report

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/today")
def get_today_analysis(db: Session = Depends(get_db)):
    """取得今日市場分析報告（有快取則直接回傳）"""
    today = str(date.today())
    existing = db.query(DailyReportModel).filter(DailyReportModel.date == today).first()
    if existing:
        return {"date": today, "content": existing.content, "cached": True}

    return generate_and_save_report(today, db)


@router.post("/refresh")
def refresh_today_analysis(db: Session = Depends(get_db)):
    """強制重新生成今日分析報告"""
    today = str(date.today())
    existing = db.query(DailyReportModel).filter(DailyReportModel.date == today).first()
    if existing:
        db.delete(existing)
        db.commit()
    return generate_and_save_report(today, db)


@router.get("/{report_date}")
def get_analysis_by_date(report_date: str, db: Session = Depends(get_db)):
    """取得指定日期的分析報告（格式：YYYY-MM-DD）"""
    report = db.query(DailyReportModel).filter(DailyReportModel.date == report_date).first()
    if not report:
        return {"date": report_date, "content": "該日期尚無分析報告", "cached": False}
    return {"date": report.date, "content": report.content, "cached": True}


def generate_and_save_report(report_date: str, db: Session):
    quotes = fetch_all_quotes()
    news = fetch_news(limit=15)
    content = generate_daily_report(
        us_stocks=quotes.get("US", []),
        tw_stocks=quotes.get("TW", []),
        news=news,
    )
    record = DailyReportModel(date=report_date, content=content)
    db.add(record)
    db.commit()
    return {"date": report_date, "content": content, "cached": False}
