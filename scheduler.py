from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date
from database import SessionLocal, DailyReport as DailyReportModel
from services.stock_service import fetch_all_quotes
from services.news_service import fetch_news
from services.ai_service import generate_daily_report


def run_daily_update():
    print("[scheduler] 開始每日資料更新...")
    today = str(date.today())
    db = SessionLocal()
    try:
        existing = db.query(DailyReportModel).filter(DailyReportModel.date == today).first()
        if existing:
            print(f"[scheduler] {today} 的報告已存在，跳過")
            return

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
        print(f"[scheduler] {today} 分析報告已生成並儲存")
    except Exception as e:
        print(f"[scheduler] 每日更新失敗：{e}")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    # 每天台灣時間 18:30（UTC+8）更新，對應 UTC 10:30
    scheduler.add_job(
        run_daily_update,
        CronTrigger(hour=10, minute=30, timezone="UTC"),
        id="daily_update",
        replace_existing=True,
    )
    scheduler.start()
    print("[scheduler] 排程已啟動（每日 18:30 台灣時間自動更新）")
    return scheduler
