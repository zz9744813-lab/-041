from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.project import Project
from app.models.story import StoryBible, Character, Volume
from app.models.chapter import Chapter, ChapterVersion
from app.models.job import GenerationJob
from app.models.model_config import ModelConfig
from app.template_utils import templates
import os

router = APIRouter()

@router.get("/")
def root():
    return RedirectResponse(url="/projects")

@router.get("/projects")
def project_list(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    result = []
    for p in projects:
        ch_count = db.query(func.count(Chapter.id)).filter(Chapter.project_id == p.id).scalar() or 0
        word_count = db.query(func.coalesce(func.sum(Chapter.actual_words), 0)).filter(Chapter.project_id == p.id).scalar() or 0
        result.append({"id": p.id, "title": p.title, "genre": p.genre, "style": p.style, "status": p.status, "idea": p.idea or "", "chapter_count": ch_count, "total_words": word_count})
    return templates.TemplateResponse("projects.html", {"request": request, "projects": result})

@router.get("/projects/new")
def new_project_form(request: Request):
    return templates.TemplateResponse("project_new.html", {"request": request})

@router.post("/projects/new")
def create_project(request: Request, title: str = Form(...), idea: str = Form(""), genre: str = Form(""), style: str = Form(""), target_words: int = Form(50000), db: Session = Depends(get_db)):
    project = Project(title=title, idea=idea, genre=genre, style=style, target_words=target_words)
    db.add(project)
    db.commit()
    return RedirectResponse(url=f"/projects/{project.id}", status_code=303)

@router.get("/projects/{project_id}")
def project_detail(request: Request, project_id: str, error: str = "", db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return templates.TemplateResponse("projects.html", {"request": request, "projects": [], "error": "项目不存在"})
    bible = db.query(StoryBible).filter(StoryBible.project_id == project_id).first()
    characters = db.query(Character).filter(Character.project_id == project_id).order_by(Character.name).all()
    volumes = db.query(Volume).filter(Volume.project_id == project_id).order_by(Volume.volume_number).all()
    chapters = db.query(Chapter).filter(Chapter.project_id == project_id).order_by(Chapter.chapter_number).all()
    total_chapters = len(chapters)
    total_words = db.query(func.coalesce(func.sum(Chapter.actual_words), 0)).filter(Chapter.project_id == project_id).scalar() or 0
    return templates.TemplateResponse("project_detail.html", {"request": request, "project": project, "bible": bible, "characters": characters, "volumes": volumes, "chapters": chapters, "total_chapters": total_chapters, "total_words": total_words, "error": error})

@router.get("/projects/{project_id}/chapters/{chapter_id}")
def chapter_detail(request: Request, project_id: str, chapter_id: str, error: str = "", success: str = "", db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.project_id == project_id).first()
    if not project or not chapter:
        return RedirectResponse(url="/projects")
    versions = db.query(ChapterVersion).filter(ChapterVersion.chapter_id == chapter_id).order_by(ChapterVersion.version_number.desc()).all()
    current_version = None
    if chapter.current_version_id:
        current_version = db.query(ChapterVersion).filter(ChapterVersion.id == chapter.current_version_id).first()
    return templates.TemplateResponse("chapter_detail.html", {"request": request, "project": project, "chapter": chapter, "versions": versions, "current_version": current_version, "error": error, "success": success})

@router.get("/jobs")
def job_list(request: Request, status: str = "", db: Session = Depends(get_db)):
    query = db.query(GenerationJob).order_by(GenerationJob.created_at.desc())
    if status:
        query = query.filter(GenerationJob.status == status)
    jobs_list = query.limit(100).all()
    return templates.TemplateResponse("jobs.html", {"request": request, "jobs": jobs_list, "current_status": status})

@router.get("/settings")
def settings_page(request: Request, success: str = "", error: str = "", db: Session = Depends(get_db)):
    models = db.query(ModelConfig).order_by(ModelConfig.is_default.desc(), ModelConfig.name).all()
    return templates.TemplateResponse("settings.html", {"request": request, "models": models, "success": success, "error": error})

@router.get("/exports")
def exports_page(request: Request, project_id: str = "", db: Session = Depends(get_db)):
    export_files = []
    export_dir = os.path.join(os.path.dirname(__file__), "..", "..", "exports")
    if os.path.exists(export_dir):
        for f in sorted(os.listdir(export_dir), reverse=True)[:20]:
            fpath = os.path.join(export_dir, f)
            if os.path.isfile(fpath):
                size = os.path.getsize(fpath)
                export_files.append({"name": f, "size": f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"})
    return templates.TemplateResponse("exports.html", {"request": request, "project_id": project_id, "export_files": export_files})
