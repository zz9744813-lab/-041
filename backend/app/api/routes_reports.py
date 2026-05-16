"""Reports endpoints (daily/weekly stubs - implementation in Step 10)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()


@router.get("/daily")
def daily_report(date: str | None = None, db: Session = Depends(get_db)):
    return {"date": date, "summary": "stub - implemented in Step 10"}


@router.get("/weekly")
def weekly_report(week: str | None = None, db: Session = Depends(get_db)):
    return {"week": week, "summary": "stub"}


@router.post("/generate-daily")
def generate_daily_now(db: Session = Depends(get_db)):
    from app.jobs.daily_report_job import run

    return {"ok": True, "stats": run()}
