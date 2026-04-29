import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Project, Character, StoryBible, Volume, Chapter, GenerationJob
from app.services.llm_client import LLMClient, get_default_model
from app.services.setting_service import load_prompt

logger = logging.getLogger(__name__)


def generate_outline(project_id: str, db: Session) -> GenerationJob:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    bible = db.query(StoryBible).filter(StoryBible.project_id == project_id).first()
    characters = db.query(Character).filter(Character.project_id == project_id).all()

    config = get_default_model(db)
    if not config:
        raise ValueError("No default model configured")

    job = GenerationJob(
        project_id=project_id,
        job_type="outline",
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        project.status = "generating"
        db.commit()

        prompt = load_prompt("outline_generator.md") or "你是一个专业的小说大纲生成器。根据设定生成分卷和章节大纲。"
        bible_text = f"世界观：{bible.world_view}\n力量体系：{bible.magic_system}\n主线：{bible.main_plot}\n主题：{bible.theme}\n文风：{bible.tone}" if bible else "无设定"
        chars_text = "\n".join([f"- {c.name}: {c.personality}" for c in characters]) if characters else "无角色"
        user_input = f"小说标题：{project.title}\n\n设定：\n{bible_text}\n\n角色：\n{chars_text}\n\n目标字数：{project.target_words}"

        client = LLMClient(config, db, job)
        result = client.generate_json(prompt, user_input)

        if "error" in result:
            raise RuntimeError(f"JSON parse error: {result.get('raw', '')[:200]}")

        volumes_data = result.get("volumes", [])
        if not volumes_data:
            volumes_data = [{"title": project.title, "volume_number": 1, "description": "", "chapters": result.get("chapters", [])}]

        vol_num = 0
        ch_num = 0
        for vol_data in volumes_data:
            vol_num += 1
            vol = Volume(
                project_id=project_id,
                title=vol_data.get("title", f"第{vol_num}卷"),
                volume_number=vol_num,
                description=vol_data.get("description", "")
            )
            db.add(vol)
            db.flush()

            for ch_data in vol_data.get("chapters", []):
                ch_num += 1
                ch = Chapter(
                    project_id=project_id,
                    volume_id=vol.id,
                    title=ch_data.get("title", f"第{ch_num}章"),
                    chapter_number=ch_num,
                    outline=ch_data.get("outline", ch_data.get("description", "")),
                    status="planned",
                    target_words=ch_data.get("target_words", 2000)
                )
                db.add(ch)

        project.status = "outline_generated"
        job.status = "completed"
        job.progress = 100
        job.output_text = json.dumps(result, ensure_ascii=False, indent=2)[:5000]
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job

    except Exception as e:
        project.status = "failed"
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
