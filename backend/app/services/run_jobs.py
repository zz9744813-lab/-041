"""Background job runner with in-memory status tracking + an SSE pub/sub hub.

This is a lightweight dependency-free job tracker; for a production-grade
deployment swap it for RQ / Arq / Celery. The current implementation:

- POST /api/signals/run schedules `_run_generate_signals` on FastAPI's
  BackgroundTasks (which uses Starlette's task queue running in the same
  event loop / threadpool).
- The job writes progress into `_JOBS[job_id]` and publishes events to the
  per-job hub so SSE consumers can stream them.
- `get_job_status(job_id)` and `subscribe(job_id)` are the two read APIs.

The hub uses an asyncio.Queue per subscriber so multiple SSE clients can
subscribe to the same job without competing for messages.
"""
from __future__ import annotations

import asyncio
import threading
import time
import uuid
from collections import defaultdict
from contextlib import contextmanager
from typing import Any

from fastapi import BackgroundTasks
from loguru import logger


# ----- in-memory state -----

_JOBS: dict[str, dict[str, Any]] = {}
"""job_id -> {status, started_at, finished_at, asset_total, asset_done,
              current_symbol, error, result}"""

_LOCK = threading.RLock()


# ----- pub/sub for SSE -----


class _Hub:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._history: dict[str, list[dict]] = defaultdict(list)
        self._lock = threading.RLock()
        # Cap history per-job so a forgotten run doesn't leak memory.
        self._max_history = 2000

    def publish(self, job_id: str, event: dict) -> None:
        with self._lock:
            history = self._history[job_id]
            history.append(event)
            if len(history) > self._max_history:
                del history[: len(history) - self._max_history]
            queues = list(self._subscribers.get(job_id, ()))
        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest in the slow consumer's queue.
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    pass

    def history(self, job_id: str) -> list[dict]:
        with self._lock:
            return list(self._history.get(job_id, ()))

    @contextmanager
    def subscribe(self, job_id: str):
        q: asyncio.Queue = asyncio.Queue(maxsize=512)
        with self._lock:
            self._subscribers[job_id].append(q)
        try:
            yield q
        finally:
            with self._lock:
                if q in self._subscribers.get(job_id, []):
                    self._subscribers[job_id].remove(q)
                if not self._subscribers[job_id]:
                    self._subscribers.pop(job_id, None)


HUB = _Hub()


# ----- public API -----


def get_job_status(job_id: str) -> dict | None:
    with _LOCK:
        info = _JOBS.get(job_id)
        return dict(info) if info else None


def enqueue_run_signals(background_tasks: BackgroundTasks) -> str:
    """Schedule generate_signals_job and return its job_id.

    The actual work runs in a worker thread inside the BackgroundTasks
    queue, so the HTTP response returns immediately.
    """
    job_id = str(uuid.uuid4())
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "kind": "generate_signals",
            "status": "QUEUED",
            "started_at": None,
            "finished_at": None,
            "asset_total": 0,
            "asset_done": 0,
            "current_symbol": None,
            "error": None,
            "result": None,
        }
    background_tasks.add_task(_run_generate_signals, job_id)
    HUB.publish(job_id, {"type": "queued", "job_id": job_id, "ts": time.time()})
    return job_id


def enqueue_run_review(background_tasks: BackgroundTasks, trade_id: int) -> str:
    """Schedule review_service.generate_for_trade in the background."""
    job_id = str(uuid.uuid4())
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "kind": "review",
            "trade_id": trade_id,
            "status": "QUEUED",
            "started_at": None,
            "finished_at": None,
            "error": None,
            "result": None,
        }
    background_tasks.add_task(_run_review, job_id, trade_id)
    HUB.publish(job_id, {"type": "queued", "job_id": job_id, "trade_id": trade_id, "ts": time.time()})
    return job_id


# ----- internal -----


def _set(job_id: str, **kwargs: Any) -> None:
    with _LOCK:
        info = _JOBS.get(job_id)
        if info is not None:
            info.update(kwargs)


def _run_generate_signals(job_id: str) -> None:
    """Wraps `app.jobs.generate_signals_job.run_streaming` and reports progress."""
    from app.jobs.generate_signals_job import run_streaming

    _set(job_id, status="RUNNING", started_at=time.time())
    HUB.publish(job_id, {"type": "started", "ts": time.time()})

    try:
        def on_event(event: dict) -> None:
            if event.get("type") == "asset_total":
                _set(job_id, asset_total=int(event.get("total", 0)))
            elif event.get("type") == "asset_start":
                _set(job_id, current_symbol=event.get("symbol"))
            elif event.get("type") == "asset_done":
                with _LOCK:
                    info = _JOBS.get(job_id)
                    if info is not None:
                        info["asset_done"] = int(info.get("asset_done", 0)) + 1
            HUB.publish(job_id, {**event, "ts": time.time()})

        result = run_streaming(on_event=on_event)
        _set(
            job_id,
            status="SUCCESS",
            finished_at=time.time(),
            current_symbol=None,
            result=result,
        )
        HUB.publish(job_id, {"type": "finished", "status": "SUCCESS", "ts": time.time(), "result": result})
    except Exception as e:
        logger.exception("background generate_signals failed")
        _set(
            job_id,
            status="FAILED",
            finished_at=time.time(),
            error=str(e),
        )
        HUB.publish(job_id, {"type": "finished", "status": "FAILED", "ts": time.time(), "error": str(e)})


def _run_review(job_id: str, trade_id: int) -> None:
    """Wraps `app.services.review_service.generate_for_trade` with SSE events."""
    from app.database import SessionLocal
    from app.services import review_service

    _set(job_id, status="RUNNING", started_at=time.time())
    HUB.publish(job_id, {"type": "started", "trade_id": trade_id, "ts": time.time()})

    db = SessionLocal()
    try:
        review = review_service.generate_for_trade(
            db,
            trade_id,
            on_event=lambda ev: HUB.publish(job_id, {**ev, "ts": time.time()}),
        )
        db.commit()
        result = {"review_id": review.id, "trade_id": trade_id}
        _set(job_id, status="SUCCESS", finished_at=time.time(), result=result)
        HUB.publish(job_id, {"type": "finished", "status": "SUCCESS", "ts": time.time(), "result": result})
    except Exception as e:
        db.rollback()
        logger.exception("background review failed")
        _set(job_id, status="FAILED", finished_at=time.time(), error=str(e))
        HUB.publish(job_id, {"type": "finished", "status": "FAILED", "ts": time.time(), "error": str(e)})
    finally:
        db.close()
