import json, logging, os
from sqlalchemy.orm import Session
from jinja2 import Template
from app.models.project import Project
from app.models.story import StoryBible, Character
from app.services.llm_client import LLMClient
from app.services import generation_service as gs

logger = logging.getLogger(__name__)

def generate_setting(db: Session, project_id: str) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    client = LLMClient.get_default_client(db)
    
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "setting_generator.md")
    with open(prompt_path, "r") as f:
        template_text = f.read()
    
    template = Template(template_text)
    system_prompt = template.render(
        idea=project.idea or "",
        genre=project.genre or "",
        style=project.style or ""
    )
    
    job = gs.create_job(db, project_id, None, "generate_setting")
    gs.start_job(db, job.id)
    
    try:
        result = client.generate_json(system_prompt, "请根据设定生成。")
        
        # Save story bible
        bible = StoryBible(
            project_id=project_id,
            worldview=result.get("worldview", ""),
            main_conflict=result.get("main_conflict", ""),
            theme=result.get("theme", ""),
            tone=result.get("tone", ""),
            writing_style=result.get("writing_style", ""),
            rules=result.get("rules", ""),
            raw_json=json.dumps(result, ensure_ascii=False)
        )
        db.add(bible)
        
        # Save characters
        for ch in result.get("characters", []):
            char = Character(
                project_id=project_id,
                name=ch.get("name", ""),
                role=ch.get("role", ""),
                age=ch.get("age", ""),
                appearance=ch.get("appearance", ""),
                personality=ch.get("personality", ""),
                goal=ch.get("goal", ""),
                background=ch.get("background", ""),
                relationships=ch.get("relationships", ""),
                abilities=ch.get("abilities", ""),
                forbidden_changes=ch.get("forbidden_changes", "")
            )
            db.add(char)
        
        project.status = "setting_generated"
        db.commit()
        
        gs.complete_job(db, job.id, json.dumps(result, ensure_ascii=False, indent=2))
        return result
        
    except Exception as e:
        gs.fail_job(db, job.id, str(e))
        raise