# 📈 股市儀表板

追蹤台股與美股即時報價、K線走勢，並每日自動生成中文市場分析報告。

## 功能

- 美股 / 台股即時報價與漲跌幅
- K線圖（支援 1週 / 1月 / 3月 / 6月 / 1年 / 2年 / 5年）
- 每日中文市場盤勢分析報告（由 OpenAI 生成）
- 市場新聞自動抓取（RSS）
- 每日 18:30（台灣時間）自動更新排程
- RESTful API，可供外部工具查詢

## 追蹤標的

**美股**：Amazon、Google、Meta、Microsoft、Tesla、Nvidia、Apple、TSM ADR、VOO、VT、VTI、SSO、SPY

**台股**：台積電、聯發科、台達電、鴻海、0050、0056、00878、006208、國泰金、第一金、中信金、富邦金、玉山金

## 快速開始

### 1. 設定環境變數

複製 `.env.example` 並填入 API Key：

```bash
cp .env.example .env
# 編輯 .env，填入你的 OPENAI_API_KEY
```

### 2. 建立虛擬環境並安裝套件

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 啟動伺服器

```bash
uvicorn main:app --reload --port 8000
```

### 4. 開啟瀏覽器

```
http://localhost:8000
```

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/stocks/latest` | 所有股票最新報價 |
| GET | `/api/stocks/{symbol}/latest` | 單一股票最新報價 |
| GET | `/api/stocks/{symbol}/history?period=1m` | 歷史K線資料 |
| GET | `/api/analysis/today` | 今日中文分析報告 |
| POST | `/api/analysis/refresh` | 強制重新生成報告 |
| GET | `/api/analysis/{YYYY-MM-DD}` | 指定日期報告 |
| GET | `/api/news/latest` | 最新市場新聞 |

完整 API 文件：`http://localhost:8000/docs`

## period 參數說明

`1w`（一週）｜ `1m`（一月）｜ `3m`（三月）｜ `6m`（六月）｜ `1y`（一年）｜ `2y`（兩年）｜ `5y`（五年）

## 專案結構

```
stock-dashboard/
├── main.py              # FastAPI 入口
├── config.py            # 股票代碼與設定
├── database.py          # SQLite 資料庫
├── scheduler.py         # 每日自動更新排程
├── requirements.txt
├── .env                 # 環境變數（勿上傳 Git）
├── routers/
│   ├── stocks.py        # 股票報價 API
│   ├── analysis.py      # 分析報告 API
│   └── news.py          # 新聞 API
├── services/
│   ├── stock_service.py # yfinance 資料抓取
│   ├── news_service.py  # RSS 新聞抓取
│   └── ai_service.py    # OpenAI 報告生成
├── models/
│   └── schemas.py       # Pydantic 資料模型
└── static/
    ├── index.html       # 前端主頁
    ├── style.css
    └── app.js
```

## 注意事項

- `.env` 已加入 `.gitignore`，API Key 不會被上傳
- 歷史報告會儲存在本地 `stock_data.db`（SQLite）
- 台股資料使用 yfinance，代碼格式為 `XXXX.TW`
