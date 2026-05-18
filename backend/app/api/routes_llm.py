"""SSE endpoints for streaming LLM activity to the UI.

- GET /api/llm/stream/run-signals/{job_id}
    Subscribes to events for a background generate_signals run started by
    POST /api/signals/run. Emits one SSE per asset stage so the user can
    actually watch what's happening.

- GET /api/llm/stream/decision/{symbol}
    One-off SSE: scores `symbol` with the current strategies + market
    regime, then streams the LLM call (thinking + text deltas) live, and
    finally yields the parsed SignalPlan. The result is also persisted to
    LlmCallLog so it appears in the audit log page. Does NOT actually open
    a paper trade - this is for inspection only.

The SSE format is:

    event: <name>
    data: <json>

    event: end
    data: {}
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Asset, MarketRegime
from app.services import data_service, decision_service, indicator_service, run_jobs
from app.services.run_jobs import HUB
from app.strategies import ALL_STRATEGIES, combine
from app.strategies.base import StrategyInput
from app.utils.time_utils import utc_now

router = APIRouter()


def _sse_pack(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"


# --------------------------------------------------------------------- run


@router.get("/stream/run-signals/{job_id}")
async def stream_run_signals(job_id: str):
    """Stream events for a previously-enqueued generate_signals job."""
    info = run_jobs.get_job_status(job_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_gen() -> AsyncIterator[str]:
        for ev in HUB.history(job_id):
            yield _sse_pack(ev.get("type", "message"), ev)
        with HUB.subscribe(job_id) as q:
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
                yield _sse_pack(ev.get("type", "message"), ev)
                if ev.get("type") == "finished":
                    break
        yield _sse_pack("end", {"job_id": job_id, "ts": time.time()})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/stream/review/{job_id}")
async def stream_review(job_id: str):
    """Stream thinking + text deltas for a review-regeneration job."""
    info = run_jobs.get_job_status(job_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_gen() -> AsyncIterator[str]:
        for ev in HUB.history(job_id):
            yield _sse_pack(ev.get("type", "message"), ev)
        with HUB.subscribe(job_id) as q:
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
                yield _sse_pack(ev.get("type", "message"), ev)
                if ev.get("type") == "finished":
                    break
        yield _sse_pack("end", {"job_id": job_id, "ts": time.time()})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ----------------------------------------------------------------- decision


def _build_summary(ind, candle) -> dict:
    if ind is None or candle is None:
        return {}
    close = float(candle.close)
    return {
        "close": close,
        "ma20": float(ind.ma20) if ind.ma20 else None,
        "ma50": float(ind.ma50) if ind.ma50 else None,
        "ma200": float(ind.ma200) if ind.ma200 else None,
        "rsi14": float(ind.rsi14) if ind.rsi14 else None,
        "macd_hist": float(ind.macd_hist) if ind.macd_hist else None,
        "atr14_pct": float(ind.atr14_pct) if ind.atr14_pct else None,
        "support": float(ind.support_level) if ind.support_level else None,
        "resistance": float(ind.resistance_level) if ind.resistance_level else None,
    }


@router.get("/stream/decision/{symbol}")
async def stream_decision(symbol: str):
    """Score `symbol` and stream the resulting LLM decision call live.

    This does NOT persist a Signal or open any trades. It exists so the user
    can probe a single instrument and watch the LLM think in real time.
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=512)
    loop = asyncio.get_running_loop()
    finished = threading.Event()

    def emit_to_queue(event: dict) -> None:
        # Called from the worker thread - hop back to the loop.
        try:
            asyncio.run_coroutine_threadsafe(queue.put(event), loop)
        except Exception:
            pass

    def worker() -> None:
        db = SessionLocal()
        try:
            asset = db.scalars(select(Asset).where(Asset.symbol == symbol)).first()
            if asset is None:
                emit_to_queue({"type": "error", "error": f"symbol {symbol} not found"})
                return
            now = utc_now()
            emit_to_queue({"type": "stage", "stage": "loading_candles", "symbol": symbol})
            candles_1d = data_service.candles_until(db, symbol, "1d", now, limit=300)
            candles_4h = data_service.candles_until(db, symbol, "4h", now, limit=300)
            candles_1h = data_service.candles_until(db, symbol, "1h", now, limit=300)
            if not candles_1d:
                emit_to_queue({"type": "error", "error": "no 1d candles"})
                return
            ind_1d = indicator_service.latest_snapshot(db, symbol, "1d", now)
            ind_4h = indicator_service.latest_snapshot(db, symbol, "4h", now)
            ind_1h = indicator_service.latest_snapshot(db, symbol, "1h", now)
            regime = db.scalars(
                select(MarketRegime).order_by(MarketRegime.timestamp.desc()).limit(1)
            ).first()
            si = StrategyInput(
                asset=asset,
                latest_candles_1d=candles_1d,
                latest_candles_4h=candles_4h,
                latest_candles_1h=candles_1h,
                indicators_1d=ind_1d,
                indicators_4h=ind_4h,
                indicators_1h=ind_1h,
                market_regime=regime,
                now=now,
            )
            emit_to_queue({"type": "stage", "stage": "scoring", "symbol": symbol})
            sub_scores = [s.score(si) for s in ALL_STRATEGIES]
            composite = combine(db, si, sub_scores)

            # Full breakdown so the playground can show trend / setup / risk
            # / volume / market_regime / risk_reward sub-scores per strategy.
            def _score_dict(s) -> dict:
                import dataclasses
                from decimal import Decimal as _D

                d = dataclasses.asdict(s)
                for k, v in list(d.items()):
                    if isinstance(v, _D):
                        d[k] = str(v)
                return d

            emit_to_queue(
                {
                    "type": "scores",
                    "symbol": symbol,
                    "scores": [_score_dict(s) for s in composite.all_scores],
                    "weights_applied": composite.weights_applied,
                    "regime": regime.regime if regime else None,
                }
            )
            best = composite.best_score
            if not best:
                emit_to_queue({"type": "error", "error": "no strategy score"})
                return

            current_price = candles_1d[-1].close
            from app.config import get_settings

            settings = get_settings()
            if not settings.enable_llm_decision:
                emit_to_queue(
                    {
                        "type": "info",
                        "info": "ENABLE_LLM_DECISION=false; nothing to stream.",
                    }
                )
                return

            emit_to_queue({"type": "stage", "stage": "calling_llm", "symbol": symbol})
            plan, source, log_id = decision_service.generate_signal_plan_llm(
                db,
                best,
                asset.market,
                current_price,
                regime.regime if regime else None,
                _build_summary(ind_1d, candles_1d[-1] if candles_1d else None),
                _build_summary(ind_4h, candles_4h[-1] if candles_4h else None),
                _build_summary(ind_1h, candles_1h[-1] if candles_1h else None),
                {"has_open_position": False},
                now=now,
                on_event=emit_to_queue,
            )
            if plan is None:
                emit_to_queue(
                    {"type": "result", "ok": False, "source": source, "llm_call_log_id": log_id}
                )
            else:
                emit_to_queue(
                    {
                        "type": "result",
                        "ok": True,
                        "source": source,
                        "llm_call_log_id": log_id,
                        "plan": plan.model_dump(mode="json"),
                    }
                )
        except Exception as e:
            emit_to_queue({"type": "error", "error": str(e)})
        finally:
            db.close()
            finished.set()
            # Sentinel so the SSE generator knows to break.
            try:
                asyncio.run_coroutine_threadsafe(queue.put({"__done__": True}), loop)
            except Exception:
                pass

    threading.Thread(target=worker, daemon=True).start()

    async def event_gen() -> AsyncIterator[str]:
        while True:
            try:
                ev = await asyncio.wait_for(queue.get(), timeout=15.0)
            except asyncio.TimeoutError:
                yield ": ping\n\n"
                if finished.is_set() and queue.empty():
                    break
                continue
            if ev.get("__done__"):
                break
            yield _sse_pack(ev.get("type", "message"), ev)
        yield _sse_pack("end", {"symbol": symbol, "ts": time.time()})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
