import feedparser
from models.schemas import NewsItem
from config import NEWS_FEEDS


def fetch_news(limit: int = 20) -> list[NewsItem]:
    items = []
    for feed_url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                items.append(NewsItem(
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    published=entry.get("published", ""),
                    source=feed.feed.get("title", ""),
                ))
        except Exception as e:
            print(f"[news_service] error fetching {feed_url}: {e}")

    return items[:limit]
