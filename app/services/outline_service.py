import json, logging, os
from sqlalchemy.orm import Session
from jinja2 import Template
from app.models.project import Project
from app.models.story import StoryBible, Character, Volume
from app.models.chapter import Chapter
from app.services.llm_client import LLMClient
from app.services import generation_service as gs

logger = logging.getLogger(__name__)

def generate_outline(db: Session, project_id: str) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    
    bible = db.query(StoryBible).filter(StoryBible.project_id == project_id).first()
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    
    if not bible:
        raise ValueError("Story bible not found. Generate setting first.")
    
    client = LLMClient.get_default_client(db)
    
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "outline_generator.md")
    with open(prompt_path, "r") as f:
        template_text = f.read()
    
    chars_text = "\n".join([f"- {c.name} ({c.role}): {c.personality[:100]}" for c in characters])
    
    template = Template(template_text)
    system_prompt = template.render(
        worldview=bible.worldview or "",
        main_conflict=bible.main_conflict or "",
        theme=bible.theme or "",
        tone=bible.tone or "",
        writing_style=bible.writing_style or "",
        rules=bible.rules or "",
        target_words=str(project.target_words or 50000),
        characters=chars_text
    )
    
    job = gs.create_job(db, project_id, None, "generate_outline")
    gs.start_job(db, job.id)
    
    try:
        result = client.generate_json(system_prompt, "请根据以上设定生成完整大纲。")
        
        volumes_data = result.get("volumes", [])
        for vol_data in volumes_data:
            volume = Volume(
                project_id=project_id,
                volume_number=vol_data.get("volume_number", 1),
                title=vol_data.get("title", ""),
                summary=vol_data.get("summary", ""),
                target_words=vol_data.get("target_words", project.target_words or 50000),
                status="planned"
            )
            db.add(volume)
            db.flush()
            
            for ch_data in vol_data.get("chapters", []):
                chapter = Chapter(
                    project_id=project_id,
                    volume_id=volume.id,
                    chapter_number=ch_data.get("chapter_number", 1),
                    title=ch_data.get("title", ""),
                    outline=ch_data.get("outline", ""),
                    summary="",
                    status="planned",
                    target_words=ch_data.get("target_words", 3000),
                    actual_words=0
                )
                db.add(chapter)
        
        project.status = "outline_generated"
        db.commit()
        
        gs.complete_job(db, job.id, json.dumps(result, ensure_ascii=False, indent=2))
        return result
        
    except Exception as e:
        gs.fail_job(db, job.id, str(e))
        raise