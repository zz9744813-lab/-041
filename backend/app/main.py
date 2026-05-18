"""FastAPI entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

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


# Cache-Control rules per URL prefix. Values picked so the browser/SWR can
# reuse the response on quick page switches but don't go too stale.
# `immutable` is reserved for append-only resources (LlmCallLog rows).
_CACHE_RULES: tuple[tuple[str, str], ...] = (
    # Append-only by ID -> safe to cache hard.
    ("/api/system/llm-logs/", "private, max-age=3600, immutable"),
    ("/api/system/health/", "private, max-age=60"),
    # Lists / aggregates - short cache acceptable (SWR also dedupes).
    ("/api/assets", "private, max-age=300"),
    ("/api/market/regime", "private, max-age=60"),
    ("/api/system/llm-stats", "private, max-age=60"),
    ("/api/system/llm-budget", "private, max-age=30"),
)


class CacheHeadersMiddleware(BaseHTTPMiddleware):
    """Adds Cache-Control to GET responses on stable URL prefixes.

    Skipped for SSE (text/event-stream) and any response that already sets
    its own Cache-Control header.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.method != "GET":
            return response
        if response.headers.get("Cache-Control"):
            return response
        ctype = response.headers.get("Content-Type", "")
        if ctype.startswith("text/event-stream"):
            return response
        path = request.url.path
        for prefix, value in _CACHE_RULES:
            if path == prefix or path.startswith(prefix):
                response.headers["Cache-Control"] = value
                break
        return response


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
app.add_middleware(CacheHeadersMiddleware)

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
