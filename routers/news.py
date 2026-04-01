from fastapi import APIRouter
from services.news_service import fetch_news

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/latest")
def get_latest_news(limit: int = 20):
    """取得最新市場新聞"""
    return fetch_news(limit=limit)
