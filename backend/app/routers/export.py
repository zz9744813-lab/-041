from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import PlainTextResponse
from app.database import get_db
from app import models

router = APIRouter()

@router.get("/projects/{project_id}/export/txt", response_class=PlainTextResponse)
def export_project_txt(project_id: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chapters = db.query(models.Chapter).filter(models.Chapter.project_id == project_id).order_by(models.Chapter.chapter_number).all()
    
    lines = []
    lines.append(f"# {project.title}")
    lines.append("\n")
    if project.description:
        lines.append(project.description)
        lines.append("\n")
    
    for chapter in chapters:
        lines.append(f"\n## 第{chapter.chapter_number}章 {chapter.title}")
        if chapter.synopsis:
            lines.append(f"\n摘要：{chapter.synopsis}")
        if chapter.notes:
            lines.append(f"\n备注：{chapter.notes}")
        if chapter.pov:
            lines.append(f"\n视角：{chapter.pov}")
        
        # Chapter content (simulate loading from file)
        from app.utils import file_storage
        content = file_storage.read_chapter(project_id, chapter.id) or ""
        if content:
            lines.append("\n" + content)
    
    return "\n".join(lines)