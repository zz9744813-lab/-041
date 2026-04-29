import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Chapter, ChapterVersion, GenerationJob, StoryBible, Character, MemoryEntry, Project
from app.services.llm_client import LLMClient, get_default_model
from app.services.setting_service import load_prompt
from app.services.summary_service import extract_summary

logger = logging.getLogger(__name__)


def _save_version(chapter: Chapter, content: str, source: str, db: Session) -> ChapterVersion:
    versions = db.query(ChapterVersion).filter(ChapterVersion.chapter_id == chapter.id).count()
    version = ChapterVersion(
        chapter_id=chapter.id,
        version_number=versions + 1,
        content=content,
        word_count=len(content),
        source=source
    )
    db.add(version)
    db.flush()
    chapter.current_version_id = version.id
    chapter.actual_words = len(content)
    return version


def generate_chapter(chapter_id: str, db: Session) -> GenerationJob:
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise ValueError("Chapter not found")

    project = db.query(Project).filter(Project.id == chapter.project_id).first()
    bible = db.query(StoryBible).filter(StoryBible.project_id == chapter.project_id).first()
    characters = db.query(Character).filter(Character.project_id == chapter.project_id).all()

    prev_chapter = db.query(Chapter).filter(
        Chapter.project_id == chapter.project_id,
        Chapter.chapter_number < chapter.chapter_number,
        Chapter.status == "approved"
    ).order_by(Chapter.chapter_number.desc()).first()
    prev_summary = prev_chapter.summary if prev_chapter else "无"

    memories = db.query(MemoryEntry).filter(
        MemoryEntry.project_id == chapter.project_id
    ).order_by(MemoryEntry.created_at.desc()).limit(5).all()
    memory_text = "\n".join([f"- [{m.entry_type}] {m.content[:200]}" for m in memories]) if memories else "无"

    config = get_default_model(db)
    if not config:
        raise ValueError("No default model configured")

    job = GenerationJob(
        project_id=chapter.project_id,
        chapter_id=chapter_id,
        job_type="chapter",
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        chapter.status = "generating"
        db.commit()

        prompt = load_prompt("chapter_writer.md") or "你是一个专业的小说章节写手。根据设定和章节大纲，生成完整的章节正文。"
        bible_text = f"世界观：{bible.world_view}\n力量体系：{bible.magic_system}\n主线：{bible.main_plot}\n文风：{bible.tone}" if bible else "无"
        chars_text = "\n".join([f"- {c.name}: {c.personality} | 背景:{c.background[:100]}" for c in characters]) if characters else "无"

        user_input = f"""小说标题：{project.title}
文风基调：{bible.tone if bible else '未设定'}

设定参考：
{bible_text}

角色列表：
{chars_text}

前情提要：
{prev_summary}

已有记忆：
{memory_text}

当前章节：
第{chapter.chapter_number}章 {chapter.title}
章节大纲：{chapter.outline}
目标字数：{chapter.target_words}字"""

        client = LLMClient(config, db, job)
        content = client.generate_text(prompt, user_input, temperature=0.8)

        _save_version(chapter, content, "generate", db)
        chapter.status = "generated"
        chapter.word_count = len(content)

        job.status = "completed"
        job.progress = 100
        job.output_text = content[:5000]
        job.finished_at = datetime.utcnow()
        db.commit()

        try:
            extract_summary(chapter.id, db)
        except Exception:
            pass

        db.refresh(job)
        return job

    except Exception as e:
        chapter.status = "failed"
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job


def continue_chapter(chapter_id: str, continuation_prompt: str = "", db: Session = None) -> GenerationJob:
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise ValueError("Chapter not found")

    project = db.query(Project).filter(Project.id == chapter.project_id).first()

    current_content = ""
    if chapter.current_version_id:
        cv = db.query(ChapterVersion).filter(ChapterVersion.id == chapter.current_version_id).first()
        if cv:
            current_content = cv.content

    config = get_default_model(db)
    if not config:
        raise ValueError("No default model configured")

    job = GenerationJob(
        project_id=chapter.project_id,
        chapter_id=chapter_id,
        job_type="continue",
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        chapter.status = "generating"
        db.commit()

        prompt = load_prompt("chapter_writer.md") or "你是一个专业的小说续写助手。根据已有内容继续往下写。"
        tail = current_content[-3000:] if len(current_content) > 3000 else current_content
        user_input = f"""小说：{project.title}
第{chapter.chapter_number}章 {chapter.title}
章节大纲：{chapter.outline}

已有内容：
{tail}

{continuation_prompt or "请继续往下写，保持风格一致。"}"""

        client = LLMClient(config, db, job)
        content = client.generate_text(prompt, user_input, temperature=0.8)

        full_content = current_content + "\n\n" + content
        _save_version(chapter, full_content, "continue", db)
        chapter.status = "generated"
        chapter.word_count = len(full_content)

        job.status = "completed"
        job.progress = 100
        job.output_text = content[:5000]
        job.finished_at = datetime.utcnow()
        db.commit()

        db.refresh(job)
        return job

    except Exception as e:
        chapter.status = "failed"
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job


def revise_chapter(chapter_id: str, revision_instructions: str = "", db: Session = None) -> GenerationJob:
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise ValueError("Chapter not found")

    current_content = ""
    if chapter.current_version_id:
        cv = db.query(ChapterVersion).filter(ChapterVersion.id == chapter.current_version_id).first()
        if cv:
            current_content = cv.content

    config = get_default_model(db)
    if not config:
        raise ValueError("No default model configured")

    job = GenerationJob(
        project_id=chapter.project_id,
        chapter_id=chapter_id,
        job_type="revise",
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        prompt = load_prompt("chapter_reviser.md") or "你是一个专业的小说润色助手。根据要求修改章节内容。"
        user_input = f"""章节标题：{chapter.title}
章节大纲：{chapter.outline}

当前正文：
{current_content}

修改要求：
{revision_instructions or "请优化文笔，修改语病，使表达更加流畅。"}"""

        client = LLMClient(config, db, job)
        content = client.generate_text(prompt, user_input, temperature=0.7)

        _save_version(chapter, content, "revise", db)
        chapter.status = "generated"
        chapter.word_count = len(content)

        job.status = "completed"
        job.progress = 100
        job.output_text = content[:5000]
        job.finished_at = datetime.utcnow()
        db.commit()

        db.refresh(job)
        return job

    except Exception as e:
        chapter.status = "failed"
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job