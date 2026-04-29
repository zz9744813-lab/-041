import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Project, Character, StoryBible, GenerationJob
from app.services.llm_client import LLMClient, get_default_model

logger = logging.getLogger(__name__)


def load_prompt(name: str) -> str:
    prompt_dir = Path(__file__).parent.parent / "prompts"
    filepath = prompt_dir / name
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return ""


def generate_setting(project_id: str, db: Session) -> GenerationJob:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    if not project.idea:
        raise ValueError("Project has no idea set")

    config = get_default_model(db)
    if not config:
        raise ValueError("No default model configured")

    job = GenerationJob(
        project_id=project_id,
        job_type="setting",
        status="running",
        input_snapshot=json.dumps({"idea": project.idea, "genre": project.genre, "style": project.style}, ensure_ascii=False),
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        project.status = "generating"
        db.commit()

        prompt = load_prompt("setting_generator.md") or "你是一个专业的小说设定生成器。根据用户提供的创意、题材和风格，生成完整的小说设定。"
        user_input = f"创意：{project.idea}\n题材：{project.genre or '未指定'}\n风格：{project.style or '未指定'}"

        client = LLMClient(config, db, job)
        result = client.generate_json(prompt, user_input)

        if "error" in result:
            raise RuntimeError(f"JSON parse error: {result.get('raw', '')[:200]}")

        bible = StoryBible(
            project_id=project_id,
            world_view=result.get("world_view", ""),
            magic_system=result.get("magic_system", ""),
            main_plot=result.get("main_plot", ""),
            theme=result.get("theme", ""),
            tone=result.get("tone", "")
        )
        db.add(bible)

        for char_data in result.get("characters", []):
            char = Character(
                project_id=project_id,
                name=char_data.get("name", ""),
                age=char_data.get("age", ""),
                gender=char_data.get("gender", ""),
                personality=char_data.get("personality", ""),
                background=char_data.get("background", ""),
                appearance=char_data.get("appearance", ""),
                notes=char_data.get("notes", "")
            )
            db.add(char)

        project.status = "setting_generated"
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
