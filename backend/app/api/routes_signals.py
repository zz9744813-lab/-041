"""Signals endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Signal

router = APIRouter()


@router.get("")
def list_signals(
    status: str | None = None,
    symbol: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    db: Session = Depends(get_db),
):
    stmt = select(Signal).order_by(desc(Signal.created_at)).limit(limit)
    if status:
        stmt = stmt.where(Signal.status == status)
    if symbol:
        stmt = stmt.where(Signal.symbol == symbol)
    return db.scalars(stmt).all()


@router.get("/{signal_id}")
def get_signal(signal_id: int, db: Session = Depends(get_db)):
    s = db.get(Signal, signal_id)
    if not s:
        raise HTTPException(status_code=404, detail="Signal not found")
    return s


@router.post("/run")
def run_signals_now(db: Session = Depends(get_db)):
    """Manually trigger one signal generation pass.

    Implementation deferred to Step 8 (signal generation job).
    """
    from app.jobs.generate_signals_job import run as run_job

    stats = run_job()
    return {"ok": True, "stats": stats}


@router.patch("/{signal_id}/reject")
def reject_signal(signal_id: int, reason: str = "manual reject", db: Session = Depends(get_db)):
    s = db.get(Signal, signal_id)
    if not s:
        raise HTTPException(status_code=404, detail="Signal not found")
    s.status = "REJECTED"
    s.reject_reason = reason
    db.commit()
    db.refresh(s)
    return s
