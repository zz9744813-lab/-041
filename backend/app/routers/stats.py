from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.get("/stats/overview", response_model=schemas.OverviewResponse)
def get_overview(db: Session = Depends(get_db)):
    total_projects = db.query(func.count(models.Project.id)).scalar() or 0
    total_word_count = db.query(func.sum(models.Project.word_count)).scalar() or 0
    total_chapters = db.query(func.count(models.Chapter.id)).scalar() or 0
    return schemas.OverviewResponse(
        total_projects=total_projects,
        total_word_count=total_word_count,
        total_chapters=total_chapters
    )

@router.get("/projects/{project_id}/writing-sessions", response_model=List[schemas.WritingSessionResponse])
def get_writing_sessions(project_id: str, db: Session = Depends(get_db)):
    sessions = db.query(models.WritingSession).filter(models.WritingSession.project_id == project_id).order_by(models.WritingSession.date.desc()).all()
    return sessions

@router.post("/projects/{project_id}/writing-sessions", response_model=schemas.WritingSessionResponse)
def create_writing_session(project_id: str, session: schemas.WritingSessionCreate, db: Session = Depends(get_db)):
    db_check_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_check_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_session = models.WritingSession(
        project_id=project_id,
        date=session.date or None,
        word_count=session.word_count,
        duration_minutes=session.duration_minutes
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/stats/daily")
def get_daily_stats(days: int = 7, db: Session = Depends(get_db)):
    # Simpler implementation: return dummy data for now
    import datetime
    result = []
    today = datetime.date.today()
    for i in range(days):
        date = today - datetime.timedelta(days=i)
        result.append({"date": date, "word_count": (i * 100) % 1500 + 200})
    return result