"""Signals endpoints."""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Signal, Trade
from app.schemas import SignalListItem, SignalOut, TradeOut
from app.services.run_jobs import enqueue_run_signals, get_job_status

router = APIRouter()


@router.get("", response_model=list[SignalListItem])
def list_signals(
    status: str | None = None,
    symbol: str | None = None,
    reject_reason: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
):
    """List signals (light payload, no multi-KB free-text fields).

    Pagination is offset-based; default page size 50. Supports `reject_reason`
    substring filter so the System page reject-reason badges can deep-link
    into the matching signals.
    """
    stmt = select(Signal).order_by(desc(Signal.created_at)).offset(offset).limit(limit)
    if status:
        stmt = stmt.where(Signal.status == status)
    if symbol:
        stmt = stmt.where(Signal.symbol == symbol)
    if reject_reason:
        stmt = stmt.where(Signal.reject_reason.ilike(f"%{reject_reason}%"))
    return db.scalars(stmt).all()


@router.get("/{signal_id}", response_model=SignalOut)
def get_signal(signal_id: int, db: Session = Depends(get_db)):
    s = db.get(Signal, signal_id)
    if not s:
        raise HTTPException(status_code=404, detail="Signal not found")
    return s


@router.get("/{signal_id}/trade", response_model=TradeOut | None)
def get_signal_trade(signal_id: int, db: Session = Depends(get_db)):
    """Returns the trade opened from this signal, if any.

    Used by the Signal detail dialog to surface a "查看交易 #N" link for
    EXECUTED signals (and to drive the positions-page back-link).
    """
    if not db.get(Signal, signal_id):
        raise HTTPException(status_code=404, detail="Signal not found")
    stmt = select(Trade).where(Trade.signal_id == signal_id).limit(1)
    return db.scalars(stmt).first()


@router.post("/run")
def run_signals_now(background_tasks: BackgroundTasks):
    """Kick off the generate_signals_job in the background.

    Returns immediately with a job id so the UI doesn't freeze. Poll
    `GET /api/signals/run/{job_id}` for status, or for a streaming view
    use the SSE endpoint at `GET /api/llm/stream/run-signals/{job_id}`.
    """
    job_id = enqueue_run_signals(background_tasks)
    return {"ok": True, "job_id": job_id}


@router.get("/run/{job_id}")
def run_signals_status(job_id: str):
    """Poll the status of a run started by POST /api/signals/run."""
    info = get_job_status(job_id)
    if not info:
        raise HTTPException(status_code=404, detail="Job not found")
    return info


@router.patch("/{signal_id}/reject", response_model=SignalOut)
def reject_signal(signal_id: int, reason: str = "manual reject", db: Session = Depends(get_db)):
    s = db.get(Signal, signal_id)
    if not s:
        raise HTTPException(status_code=404, detail="Signal not found")
    s.status = "REJECTED"
    s.reject_reason = reason
    db.commit()
    db.refresh(s)
    return s
