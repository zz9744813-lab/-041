"""Portfolio endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PortfolioSnapshot

router = APIRouter()


@router.get("")
def current_snapshot(db: Session = Depends(get_db)):
    stmt = select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.timestamp)).limit(1)
    snap = db.scalars(stmt).first()
    if not snap:
        return None
    return snap


@router.get("/equity-curve")
def equity_curve(days: int = 180, db: Session = Depends(get_db)):
    stmt = (
        select(PortfolioSnapshot)
        .order_by(desc(PortfolioSnapshot.timestamp))
        .limit(days)
    )
    rows = db.scalars(stmt).all()
    rows.reverse()
    return [
        {"timestamp": r.timestamp.isoformat(), "equity": str(r.equity), "cash": str(r.cash)}
        for r in rows
    ]


@router.get("/drawdown")
def drawdown_series(days: int = 180, db: Session = Depends(get_db)):
    stmt = (
        select(PortfolioSnapshot)
        .order_by(desc(PortfolioSnapshot.timestamp))
        .limit(days)
    )
    rows = db.scalars(stmt).all()
    rows.reverse()
    return [
        {"timestamp": r.timestamp.isoformat(), "drawdown_pct": str(r.max_drawdown_pct)}
        for r in rows
    ]


@router.get("/exposure")
def exposure(db: Session = Depends(get_db)):
    stmt = select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.timestamp)).limit(1)
    snap = db.scalars(stmt).first()
    if not snap:
        return {"us_stock": "0", "crypto": "0"}
    return {
        "us_stock": str(snap.us_stock_exposure),
        "crypto": str(snap.crypto_exposure),
        "equity": str(snap.equity),
    }
