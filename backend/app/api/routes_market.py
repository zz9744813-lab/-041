"""Market data endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Candle, IndicatorSnapshot, MarketRegime
from app.schemas import CandleOut, IndicatorSnapshotOut

router = APIRouter()


@router.get("/candles", response_model=list[CandleOut])
def list_candles(
    symbol: str,
    timeframe: str,
    limit: Annotated[int, Query(ge=1, le=2000)] = 200,
    only_final: bool = True,
    db: Session = Depends(get_db),
):
    stmt = (
        select(Candle)
        .where(Candle.symbol == symbol, Candle.timeframe == timeframe)
        .order_by(desc(Candle.timestamp))
        .limit(limit)
    )
    if only_final:
        stmt = stmt.where(Candle.is_final.is_(True))
    rows = list(db.scalars(stmt).all())
    rows.reverse()
    return rows


@router.get("/indicators", response_model=list[IndicatorSnapshotOut])
def list_indicators(
    symbol: str,
    timeframe: str,
    latest: int = 1,
    db: Session = Depends(get_db),
):
    stmt = (
        select(IndicatorSnapshot)
        .where(IndicatorSnapshot.symbol == symbol, IndicatorSnapshot.timeframe == timeframe)
        .order_by(desc(IndicatorSnapshot.timestamp))
        .limit(latest)
    )
    return db.scalars(stmt).all()


@router.get("/regime")
def latest_regime(db: Session = Depends(get_db)):
    stmt = select(MarketRegime).order_by(desc(MarketRegime.timestamp)).limit(1)
    row = db.scalars(stmt).first()
    if not row:
        return {"regime": None, "notes": "no regime computed yet"}
    return {
        "timestamp": row.timestamp.isoformat(),
        "regime": row.regime,
        "spy_above_ma200": row.spy_above_ma200,
        "spy_above_ma50": row.spy_above_ma50,
        "vix_level": str(row.vix_level) if row.vix_level else None,
        "btc_above_ma200": row.btc_above_ma200,
        "notes": row.notes,
    }


@router.get("/regime/history")
def regime_history(days: int = 90, db: Session = Depends(get_db)):
    stmt = (
        select(MarketRegime)
        .order_by(desc(MarketRegime.timestamp))
        .limit(days)
    )
    rows = list(db.scalars(stmt).all())
    rows.reverse()
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "regime": r.regime,
        }
        for r in rows
    ]
