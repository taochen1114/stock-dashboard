from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from models.schemas import StockQuote, NewsItem
from typing import List

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def generate_daily_report(
    us_stocks: List[StockQuote],
    tw_stocks: List[StockQuote],
    news: List[NewsItem],
) -> str:
    if not client:
        return "（尚未設定 OpenAI API Key，請在 .env 檔案中設定 OPENAI_API_KEY）"

    # 整理美股資料
    us_lines = []
    for s in us_stocks:
        sign = "▲" if s.change >= 0 else "▼"
        us_lines.append(f"  {s.name}（{s.symbol}）：${s.price} {sign}{abs(s.change_pct):.2f}%")

    # 整理台股資料
    tw_lines = []
    for s in tw_stocks:
        sign = "▲" if s.change >= 0 else "▼"
        tw_lines.append(f"  {s.name}（{s.symbol}）：{s.price} {sign}{abs(s.change_pct):.2f}%")

    # 整理新聞標題
    news_lines = [f"  - {n.title}" for n in news[:10]]

    prompt = f"""你是一位專業的股市分析師，請根據以下資料，用繁體中文撰寫一份今日市場盤勢分析報告。
報告要簡潔易懂，約 300-500 字，包含：
1. 美股今日表現重點
2. 台股今日表現重點
3. 市場關鍵訊號與趨勢
4. 值得關注的新聞消息面
5. 短期展望與投資人注意事項

【今日美股資料】
{chr(10).join(us_lines)}

【今日台股資料】
{chr(10).join(tw_lines)}

【相關新聞標題】
{chr(10).join(news_lines)}

請開始撰寫報告："""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ai_service] error: {e}")
        return f"分析報告生成失敗：{str(e)}"
