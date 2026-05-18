"""Reviews endpoints."""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Review
from app.schemas import ReviewOut
from app.services.run_jobs import enqueue_run_review, get_job_status

router = APIRouter()


@router.get("", response_model=list[ReviewOut])
def list_reviews(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
):
    stmt = (
        select(Review)
        .order_by(desc(Review.created_at))
        .offset(offset)
        .limit(limit)
    )
    return db.scalars(stmt).all()


@router.get("/by-trade/{trade_id}", response_model=ReviewOut)
def get_review_by_trade(trade_id: int, db: Session = Depends(get_db)):
    """Direct trade -> review lookup; replaces client-side `find()` over the list."""
    stmt = select(Review).where(Review.trade_id == trade_id)
    r = db.scalars(stmt).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    return r


# Kept for backwards-compat: legacy frontend code still uses /api/reviews/{trade_id}.
@router.get("/{trade_id}", response_model=ReviewOut)
def get_review(trade_id: int, db: Session = Depends(get_db)):
    return get_review_by_trade(trade_id, db)


@router.post("/generate/{trade_id}")
def regenerate_review(trade_id: int, background_tasks: BackgroundTasks):
    """Schedule review regeneration in the background.

    The actual LLM call can take 5-30s; running it in the request handler
    blocks the UI and risks proxy timeout. The job runs via the same
    BackgroundTasks queue we use for /signals/run; clients can poll
    `GET /api/reviews/jobs/{job_id}` or stream via
    `GET /api/llm/stream/review/{job_id}`.
    """
    job_id = enqueue_run_review(background_tasks, trade_id)
    return {"ok": True, "job_id": job_id, "trade_id": trade_id}


@router.get("/jobs/{job_id}")
def review_job_status(job_id: str):
    info = get_job_status(job_id)
    if not info:
        raise HTTPException(status_code=404, detail="Job not found")
    return info
