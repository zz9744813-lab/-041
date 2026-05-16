"""Trades endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trade
from app.schemas import TradeOut

router = APIRouter()


@router.get("", response_model=list[TradeOut])
def list_trades(
    status: str | None = None,
    model: str | None = None,
    symbol: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    stmt = select(Trade).order_by(desc(Trade.entry_time)).limit(limit)
    if status:
        stmt = stmt.where(Trade.status == status)
    if model:
        stmt = stmt.where(Trade.model_name == model)
    if symbol:
        stmt = stmt.where(Trade.symbol == symbol)
    return db.scalars(stmt).all()


@router.get("/{trade_id}", response_model=TradeOut)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    t = db.get(Trade, trade_id)
    if not t:
        raise HTTPException(status_code=404, detail="Trade not found")
    return t


@router.post("/{trade_id}/close", response_model=TradeOut)
def close_trade_manually(trade_id: int, db: Session = Depends(get_db)):
    from app.services import paper_trading_service

    t = db.get(Trade, trade_id)
    if not t:
        raise HTTPException(status_code=404, detail="Trade not found")
    if t.status == "CLOSED":
        raise HTTPException(status_code=400, detail="Trade already closed")
    paper_trading_service.manual_close(db, t)
    db.commit()
    db.refresh(t)
    return t
