"""FastAPI entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import (
    routes_assets,
    routes_llm,
    routes_market,
    routes_models,
    routes_portfolio,
    routes_reports,
    routes_reviews,
    routes_signals,
    routes_system,
    routes_trades,
)
from app.config import get_settings
from app.utils.logging_utils import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Mini Hermes starting; provider={}", settings.llm_provider)
    yield
    logger.info("Mini Hermes shutting down")


app = FastAPI(
    title="Mini Hermes",
    description="AI 模拟交易与策略验证系统",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(routes_market.router, prefix="/api/market", tags=["market"])
app.include_router(routes_signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(routes_trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(routes_portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(routes_reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(routes_reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(routes_models.router, prefix="/api/models", tags=["models"])
app.include_router(routes_system.router, prefix="/api/system", tags=["system"])
app.include_router(routes_llm.router, prefix="/api/llm", tags=["llm"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mini-hermes"}
