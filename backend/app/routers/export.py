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
    lines.append("")
    if project.description:
        lines.append(project.description)
        lines.append("")
    
    for chapter in chapters:
        lines.append(f"\n## 第{chapter.chapter_number}章 {chapter.title}")
        if chapter.synopsis:
            lines.append(f"\n摘要：{chapter.synopsis}")
        if chapter.summary:
            lines.append(f"\nAI摘要：{chapter.summary}")
        if chapter.pov:
            lines.append(f"\n视角：{chapter.pov}")
        
        # Read from current_version
        content = ""
        if chapter.current_version_id:
            cv = db.query(models.ChapterVersion).filter(models.ChapterVersion.id == chapter.current_version_id).first()
            if cv:
                content = cv.content
        if not content:
            from app.utils import file_storage
            content = file_storage.read_chapter(project_id, chapter.id) or ""
        if content:
            lines.append("\n" + content)
    
    return "\n".join(lines)


@router.get("/projects/{project_id}/export/markdown", response_class=PlainTextResponse)
def export_project_markdown(project_id: str, db: Session = Depends(get_db)):
    """Export project as a single markdown file with frontmatter."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    volumes = db.query(models.Volume).filter(models.Volume.project_id == project_id).order_by(models.Volume.volume_number).all()
    
    lines = []
    # Frontmatter
    lines.append("---")
    lines.append(f"title: {project.title}")
    lines.append(f"genre: {project.genre or ''}")
    lines.append(f"style: {project.style or ''}")
    lines.append(f"status: {project.status}")
    lines.append(f"word_count: {project.word_count}")
    lines.append(f"created: {project.created_at.isoformat()}")
    lines.append("---")
    lines.append("")
    
    if project.description:
        lines.append(f"{project.description}")
        lines.append("")
    if project.idea:
        lines.append(f"> 创意：{project.idea}")
        lines.append("")
    
    if volumes:
        for vol in volumes:
            lines.append(f"# {vol.title}")
            lines.append("")
            if vol.description:
                lines.append(f"{vol.description}")
                lines.append("")
            chapters = db.query(models.Chapter).filter(
                models.Chapter.volume_id == vol.id
            ).order_by(models.Chapter.chapter_number).all()
            for ch in chapters:
                lines.append(f"## 第{ch.chapter_number}章 {ch.title}")
                if ch.outline:
                    lines.append(f"\n> 大纲：{ch.outline}\n")
                content = ""
                if ch.current_version_id:
                    cv = db.query(models.ChapterVersion).filter(models.ChapterVersion.id == ch.current_version_id).first()
                    if cv:
                        content = cv.content
                if content:
                    lines.append("\n" + content)
                lines.append("")
    else:
        # Fallback: no volumes
        chapters = db.query(models.Chapter).filter(models.Chapter.project_id == project_id).order_by(models.Chapter.chapter_number).all()
        for ch in chapters:
            lines.append(f"## 第{ch.chapter_number}章 {ch.title}")
            content = ""
            if ch.current_version_id:
                cv = db.query(models.ChapterVersion).filter(models.ChapterVersion.id == ch.current_version_id).first()
                if cv:
                    content = cv.content
            if content:
                lines.append("\n" + content)
            lines.append("")
    
    return "\n".join(lines)