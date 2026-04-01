from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from database import init_db
from routers import stocks, analysis, news
from scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="股市儀表板",
    description="台股 & 美股即時追蹤與分析",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(stocks.router)
app.include_router(analysis.router)
app.include_router(news.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
