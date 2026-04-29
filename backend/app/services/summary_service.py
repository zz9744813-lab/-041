import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Chapter, ChapterVersion, MemoryEntry
from app.services.llm_client import LLMClient, get_default_model
from app.services.setting_service import load_prompt

logger = logging.getLogger(__name__)


def extract_summary(chapter_id: str, db: Session) -> Optional[Chapter]:
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        return None

    content = ""
    if chapter.current_version_id:
        cv = db.query(ChapterVersion).filter(ChapterVersion.id == chapter.current_version_id).first()
        if cv:
            content = cv.content

    if not content.strip():
        return chapter

    config = get_default_model(db)
    if not config:
        logger.warning("No default model configured, skipping summary")
        return chapter

    prompt = load_prompt("summary_extractor.md") or "请用100-200字概括以下章节的主要内容。"
    user_input = f"第{chapter.chapter_number}章 {chapter.title}\n\n{content[:3000]}"

    try:
        client = LLMClient(config, db)
        summary = client.generate_text(prompt, user_input, temperature=0.3)
        chapter.summary = summary.strip()

        memory = MemoryEntry(
            project_id=chapter.project_id,
            chapter_id=chapter_id,
            content=f"第{chapter.chapter_number}章 {chapter.title}: {summary[:300]}",
            entry_type="summary"
        )
        db.add(memory)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to extract summary: {e}")

    return chapter
