from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.models.story import StoryBible, Character, Volume
from app.models.chapter import Chapter, ChapterVersion
from app.models.job import GenerationJob
from app.models.usage import ApiUsageLog
from app.models.model_config import ModelConfig
from app.models.memory import MemoryEntry
from app.services import setting_service, outline_service, chapter_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/projects/{project_id}/delete")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return RedirectResponse(url="/projects", status_code=303)
    ids_to_delete = {"project": project_id}
    db.query(MemoryEntry).filter(MemoryEntry.project_id == project_id).delete()
    db.query(ApiUsageLog).filter(ApiUsageLog.project_id == project_id).delete()
    db.query(GenerationJob).filter(GenerationJob.project_id == project_id).delete()
    ch_versions = db.query(ChapterVersion).join(Chapter).filter(Chapter.project_id == project_id).all()
    for cv in ch_versions:
        db.delete(cv)
    db.query(Chapter).filter(Chapter.project_id == project_id).delete()
    db.query(Volume).filter(Volume.project_id == project_id).delete()
    db.query(Character).filter(Character.project_id == project_id).delete()
    db.query(StoryBible).filter(StoryBible.project_id == project_id).delete()
    db.delete(project)
    db.commit()
    return RedirectResponse(url="/projects", status_code=303)

@router.post("/projects/{project_id}/generate-setting")
def generate_setting(project_id: str, db: Session = Depends(get_db)):
    try:
        setting_service.generate_setting(db, project_id)
        return RedirectResponse(url=f"/projects/{project_id}", status_code=303)
    except Exception as e:
        logger.error(f"Generate setting failed: {e}")
        return RedirectResponse(url=f"/projects/{project_id}?error={str(e)}", status_code=303)

@router.post("/projects/{project_id}/generate-outline")
def generate_outline(project_id: str, db: Session = Depends(get_db)):
    try:
        outline_service.generate_outline(db, project_id)
        return RedirectResponse(url=f"/projects/{project_id}", status_code=303)
    except Exception as e:
        logger.error(f"Generate outline failed: {e}")
        return RedirectResponse(url=f"/projects/{project_id}?error={str(e)}", status_code=303)

@router.post("/projects/{project_id}/generate-next-chapter")
def generate_next_chapter(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return RedirectResponse(url="/projects", status_code=303)
    chapter = db.query(Chapter).filter(
        Chapter.project_id == project_id,
        Chapter.status.in_(["planned", "failed"])
    ).order_by(Chapter.chapter_number).first()
    if not chapter:
        return RedirectResponse(url=f"/projects/{project_id}?error=已经没有等待生成的章节", status_code=303)
    try:
        project.status = "generating"
        db.commit()
        chapter_service.generate_chapter(db, project_id, chapter.id)
        return RedirectResponse(url=f"/projects/{project_id}", status_code=303)
    except Exception as e:
        project.status = "failed"
        db.commit()
        logger.error(f"Generate chapter failed: {e}")
        return RedirectResponse(url=f"/projects/{project_id}?error={str(e)}", status_code=303)

@router.post("/projects/{project_id}/pause")
def toggle_pause(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return RedirectResponse(url="/projects", status_code=303)
    if project.status == "generating":
        project.status = "paused"
    elif project.status == "paused":
        project.status = "generating"
    db.commit()
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

@router.post("/projects/{project_id}/batch-generate")
def batch_generate(project_id: str, start: int = Form(1), end: int = Form(1), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return RedirectResponse(url="/projects", status_code=303)
    chapters = db.query(Chapter).filter(
        Chapter.project_id == project_id,
        Chapter.chapter_number >= start,
        Chapter.chapter_number <= end,
        Chapter.status.in_(["planned", "failed"])
    ).order_by(Chapter.chapter_number).all()
    
    project.status = "generating"
    db.commit()
    
    for ch in chapters:
        try:
            chapter_service.generate_chapter(db, project_id, ch.id)
        except Exception as e:
            logger.error(f"Batch: chapter {ch.chapter_number} failed: {e}")
            break
    
    project.status = "outline_generated"
    db.commit()
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)
