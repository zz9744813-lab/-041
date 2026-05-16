"""Reviews endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Review

router = APIRouter()


@router.get("")
def list_reviews(limit: int = 50, db: Session = Depends(get_db)):
    stmt = select(Review).order_by(desc(Review.created_at)).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{trade_id}")
def get_review(trade_id: int, db: Session = Depends(get_db)):
    stmt = select(Review).where(Review.trade_id == trade_id)
    r = db.scalars(stmt).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    return r


@router.post("/generate/{trade_id}")
def regenerate_review(trade_id: int, db: Session = Depends(get_db)):
    from app.services import review_service

    review = review_service.generate_for_trade(db, trade_id)
    db.commit()
    db.refresh(review)
    return review
