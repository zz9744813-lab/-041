"""Models endpoints per spec § 18.8."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ModelStat, StrategyModel, Trade
from app.schemas import ModelStatOut, StrategyModelOut, TradeOut

router = APIRouter()


@router.get("", response_model=list[StrategyModelOut])
def list_models(db: Session = Depends(get_db)):
    return db.scalars(select(StrategyModel).order_by(StrategyModel.name)).all()


@router.get("/{name}/stats", response_model=ModelStatOut)
def model_stats(name: str, window: str = "LAST_30D", db: Session = Depends(get_db)):
    stmt = select(ModelStat).where(ModelStat.model_name == name, ModelStat.window == window)
    s = db.scalars(stmt).first()
    if not s:
        raise HTTPException(status_code=404, detail="No stats yet")
    return s


@router.patch("/{name}", response_model=StrategyModelOut)
def update_model(
    name: str,
    weight: float | None = None,
    auto_adjust: bool | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(StrategyModel).where(StrategyModel.name == name)
    m = db.scalars(stmt).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    if weight is not None:
        m.weight = weight
    if auto_adjust is not None:
        m.auto_adjust_weight = auto_adjust
    if is_active is not None:
        m.is_active = is_active
    db.commit()
    db.refresh(m)
    return m


@router.get("/{name}/recent-trades", response_model=list[TradeOut])
def recent_trades(name: str, limit: int = 50, db: Session = Depends(get_db)):
    stmt = (
        select(Trade)
        .where(Trade.model_name == name)
        .order_by(desc(Trade.entry_time))
        .limit(limit)
    )
    return db.scalars(stmt).all()
