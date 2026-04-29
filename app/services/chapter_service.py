import json, logging, os
from typing import Optional, List
from sqlalchemy.orm import Session
from jinja2 import Template
from app.models.project import Project
from app.models.story import StoryBible, Character
from app.models.chapter import Chapter, ChapterVersion
from app.services.llm_client import LLMClient
from app.services import generation_service as gs
from app.services import summary_service as ss

logger = logging.getLogger(__name__)

def _build_context(db: Session, project_id: str, chapter_id: str) -> dict:
    """Build context for chapter generation."""
    bible = db.query(StoryBible).filter(StoryBible.project_id == project_id).first()
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    
    prev_chapters = db.query(Chapter).filter(
        Chapter.project_id == project_id,
        Chapter.chapter_number < chapter.chapter_number,
        Chapter.status == "approved"
    ).order_by(Chapter.chapter_number.desc()).limit(5).all()
    
    prev_summaries = []
    for pc in reversed(prev_chapters):
        prev_summaries.append(f"第{pc.chapter_number}章 {pc.title}: {pc.summary or '无摘要'}")
    
    chars_text = "\n".join([
        f"- {c.name} ({c.role}): {c.personality[:200]}"
        for c in characters
    ])
    
    return {
        "bible": bible,
        "characters_text": chars_text,
        "chapter": chapter,
        "prev_summaries": "\n".join(prev_summaries) if prev_summaries else "（这是第一章）"
    }

def _save_version(db: Session, chapter_id: str, content: str, source: str, model_config_id: Optional[str] = None):
    """Create a new chapter version."""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise ValueError("Chapter not found")
    
    # Get next version number
    latest = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id
    ).order_by(ChapterVersion.version_number.desc()).first()
    next_ver = (latest.version_number + 1) if latest else 1
    
    version = ChapterVersion(
        chapter_id=chapter_id,
        version_number=next_ver,
        content=content,
        source=source,
        model_config_id=model_config_id,
        word_count=len(content.split()) if content else 0
    )
    db.add(version)
    db.flush()
    
    chapter.current_version_id = version.id
    chapter.actual_words = version.word_count
    chapter.status = "generated"
    db.commit()
    return version

def generate_chapter(db: Session, project_id: str, chapter_id: str) -> dict:
    """Generate chapter content."""
    project = db.query(Project).filter(Project.id == project_id).first()
    client = LLMClient.get_default_client(db)
    context = _build_context(db, project_id, chapter_id)
    chapter = context["chapter"]
    bible = context["bible"]
    
    if not bible:
        raise ValueError("Story bible not found. Generate setting first.")
    if not chapter.outline:
        raise ValueError("Chapter outline not found. Generate outline first.")
    
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "chapter_writer.md")
    with open(prompt_path, "r") as f:
        template_text = f.read()
    
    template = Template(template_text)
    system_prompt = template.render(
        title=project.title,
        worldview=bible.worldview or "",
        main_conflict=bible.main_conflict or "",
        theme=bible.theme or "",
        tone=bible.tone or "",
        writing_style=bible.writing_style or "",
        rules=bible.rules or "",
        characters=context["characters_text"],
        chapter_title=chapter.title,
        chapter_outline=chapter.outline or "",
        prev_summaries=context["prev_summaries"],
        target_words=str(chapter.target_words or 3000)
    )
    
    job = gs.create_job(db, project_id, chapter_id, "generate_chapter")
    gs.start_job(db, job.id)
    
    try:
        content = client.generate_text(system_prompt, "请根据以上要求创作本章正文。")
        
        # Save version
        config = db.query(Job).filter(Job.id == ...).first()  # simplified
        version = _save_version(db, chapter_id, content, "generated", None)
        
        db.commit()
        gs.complete_job(db, job.id, content[:500] + "...")
        
        # Auto-summarize
        try:
            ss.extract_summary(db, project_id, chapter_id)
        except Exception as e:
            logger.warning(f"Auto-summarize failed: {e}")
        
        return {"chapter_id": chapter_id, "version_id": version.id, "word_count": version.word_count, "content_preview": content[:200]}
        
    except Exception as e:
        chapter.status = "failed"
        db.commit()
        gs.fail_job(db, job.id, str(e))
        raise

def revise_chapter(db: Session, project_id: str, chapter_id: str) -> dict:
    """Revise/polish chapter content."""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter or not chapter.current_version_id:
        raise ValueError("No chapter version to revise")
    
    version = db.query(ChapterVersion).filter(ChapterVersion.id == chapter.current_version_id).first()
    bible = db.query(StoryBible).filter(StoryBible.project_id == project_id).first()
    
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "chapter_reviser.md")
    with open(prompt_path, "r") as f:
        template_text = f.read()
    
    template = Template(template_text)
    system_prompt = template.render(
        tone=bible.tone if bible else "",
        writing_style=bible.writing_style if bible else "",
        content=version.content
    )
    
    client = LLMClient.get_default_client(db)
    job = gs.create_job(db, project_id, chapter_id, "revise_chapter")
    gs.start_job(db, job.id)
    
    try:
        revised = client.generate_text(system_prompt, "请在保持原剧情不变的前提下进行润色。")
        new_version = _save_version(db, chapter_id, revised, "revised", None)
        db.commit()
        gs.complete_job(db, job.id, revised[:500])
        return {"version_id": new_version.id, "word_count": new_version.word_count}
    except Exception as e:
        gs.fail_job(db, job.id, str(e))
        raise

def save_manual_version(db: Session, chapter_id: str, content: str) -> dict:
    """Save a manual edit as a new version."""
    version = _save_version(db, chapter_id, content, "manual", None)
    return {"version_id": version.id, "version_number": version.version_number, "word_count": version.word_count}

def get_versions(db: Session, chapter_id: str) -> List[ChapterVersion]:
    return db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id
    ).order_by(ChapterVersion.created_at.desc()).all()

def switch_version(db: Session, chapter_id: str, version_id: str):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    version = db.query(ChapterVersion).filter(ChapterVersion.id == version_id).first()
    if not chapter or not version:
        raise ValueError("Chapter or version not found")
    if version.chapter_id != chapter_id:
        raise ValueError("Version does not belong to this chapter")
    chapter.current_version_id = version_id
    chapter.actual_words = version.word_count
    db.commit()