import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Chapter, ChapterVersion, StoryBible, Character, GenerationJob
from app.services.llm_client import LLMClient, get_default_model
from app.services.setting_service import load_prompt

logger = logging.getLogger(__name__)


def check_consistency(chapter_id: str, db: Session) -> GenerationJob:
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise ValueError("Chapter not found")

    bible = db.query(StoryBible).filter(StoryBible.project_id == chapter.project_id).first()
    characters = db.query(Character).filter(Character.project_id == chapter.project_id).all()

    content = ""
    if chapter.current_version_id:
        cv = db.query(ChapterVersion).filter(ChapterVersion.id == chapter.current_version_id).first()
        if cv:
            content = cv.content

    config = get_default_model(db)
    if not config:
        raise ValueError("No default model configured")

    job = GenerationJob(
        project_id=chapter.project_id,
        chapter_id=chapter_id,
        job_type="consistency",
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        prompt = load_prompt("consistency_checker.md") or "检查以下章节内容是否与设定一致，指出矛盾之处。"
        bible_text = f"世界观：{bible.world_view}\n力量体系：{bible.magic_system}\n主线：{bible.main_plot}" if bible else "无"
        chars_text = "\n".join([f"- {c.name}: {c.personality}" for c in characters]) if characters else "无"
        user_input = f"设定：\n{bible_text}\n\n角色设定：\n{chars_text}\n\n章节内容（第{chapter.chapter_number}章 {chapter.title}）：\n{content[:5000]}"

        client = LLMClient(config, db, job)
        result = client.generate_text(prompt, user_input, temperature=0.3)

        job.status = "completed"
        job.progress = 100
        job.output_text = result
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
