import os, logging
from typing import Tuple
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.chapter import Chapter, ChapterVersion

logger = logging.getLogger(__name__)

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "exports")

def _ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)

def export_txt(db: Session, project_id: str) -> Tuple[str, str]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    
    chapters = db.query(Chapter).filter(
        Chapter.project_id == project_id
    ).order_by(Chapter.chapter_number).all()
    
    _ensure_export_dir()
    safe_name = project.title.replace(" ", "_").replace("/", "_") or "untitled"
    filename = f"{safe_name}.txt"
    filepath = os.path.join(EXPORT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{project.title}\n")
        f.write(f"{'='*50}\n\n")
        if project.idea:
            f.write(f"创意：{project.idea}\n\n")
        
        for ch in chapters:
            if not ch.current_version_id:
                continue
            version = db.query(ChapterVersion).filter(ChapterVersion.id == ch.current_version_id).first()
            if not version:
                continue
            f.write(f"\n第{ch.chapter_number}章 {ch.title}\n")
            f.write(f"{'-'*30}\n")
            f.write(version.content if version.content else "")
            f.write("\n\n")
    
    return filepath, filename

def export_markdown(db: Session, project_id: str) -> Tuple[str, str]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    
    chapters = db.query(Chapter).filter(
        Chapter.project_id == project_id
    ).order_by(Chapter.chapter_number).all()
    
    _ensure_export_dir()
    safe_name = project.title.replace(" ", "_").replace("/", "_") or "untitled"
    filename = f"{safe_name}.md"
    filepath = os.path.join(EXPORT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {project.title}\n\n")
        if project.idea:
            f.write(f"> 创意：{project.idea}\n\n")
        
        for ch in chapters:
            if not ch.current_version_id:
                continue
            version = db.query(ChapterVersion).filter(ChapterVersion.id == ch.current_version_id).first()
            if not version:
                continue
            f.write(f"## 第{ch.chapter_number}章 {ch.title}\n\n")
            if ch.summary:
                f.write(f"> {ch.summary}\n\n")
            f.write(version.content if version.content else "")
            f.write("\n\n---\n\n")
    
    return filepath, filename