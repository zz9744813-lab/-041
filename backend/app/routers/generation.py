from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Project, Chapter, GenerationJob
from app.schemas import GenerationJobResponse

router = APIRouter()


@router.post("/projects/{project_id}/generate-setting", response_model=GenerationJobResponse)
def api_generate_setting(project_id: str, db: Session = Depends(get_db)):
    from app.services.setting_service import generate_setting
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.idea:
        raise HTTPException(status_code=400, detail="Project must have an idea set first")
    try:
        job = generate_setting(project_id, db)
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/generate-outline", response_model=GenerationJobResponse)
def api_generate_outline(project_id: str, db: Session = Depends(get_db)):
    from app.services.outline_service import generate_outline
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        job = generate_outline(project_id, db)
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/generate-all", response_model=List[GenerationJobResponse])
def api_generate_all(project_id: str, db: Session = Depends(get_db)):
    """Generate setting + outline in sequence."""
    from app.services.setting_service import generate_setting
    from app.services.outline_service import generate_outline
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    jobs = []
    if project.status == "idea":
        job1 = generate_setting(project_id, db)
        jobs.append(job1)
        db.refresh(project)
    if project.status in ("setting_generated", "idea"):
        job2 = generate_outline(project_id, db)
        jobs.append(job2)
    return jobs


@router.post("/chapters/{chapter_id}/generate", response_model=GenerationJobResponse)
def api_generate_chapter(chapter_id: str, db: Session = Depends(get_db)):
    from app.services.chapter_service import generate_chapter
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    try:
        job = generate_chapter(chapter_id, db)
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chapters/{chapter_id}/continue", response_model=GenerationJobResponse)
def api_continue_chapter(chapter_id: str, continuation_prompt: str = "", db: Session = Depends(get_db)):
    from app.services.chapter_service import continue_chapter
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    try:
        job = continue_chapter(chapter_id, continuation_prompt, db)
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chapters/{chapter_id}/revise", response_model=GenerationJobResponse)
def api_revise_chapter(chapter_id: str, revision_instructions: str = "", db: Session = Depends(get_db)):
    from app.services.chapter_service import revise_chapter
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    try:
        job = revise_chapter(chapter_id, revision_instructions, db)
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chapters/{chapter_id}/check-consistency", response_model=GenerationJobResponse)
def api_check_consistency(chapter_id: str, db: Session = Depends(get_db)):
    from app.services.consistency_service import check_consistency
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    try:
        job = check_consistency(chapter_id, db)
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
