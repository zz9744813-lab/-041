import json, logging, os
from sqlalchemy.orm import Session
from jinja2 import Template
from app.models.story import StoryBible, Character
from app.models.chapter import Chapter, ChapterVersion
from app.services.llm_client import LLMClient
from app.services import generation_service as gs

logger = logging.getLogger(__name__)

def check_consistency(db: Session, project_id: str, chapter_id: str) -> dict:
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter or not chapter.current_version_id:
        raise ValueError("Chapter has no content")
    
    version = db.query(ChapterVersion).filter(ChapterVersion.id == chapter.current_version_id).first()
    bible = db.query(StoryBible).filter(StoryBible.project_id == project_id).first()
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    
    client = LLMClient.get_default_client(db)
    
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "consistency_checker.md")
    with open(prompt_path, "r") as f:
        template_text = f.read()
    
    chars_text = "\n".join([f"- {c.name} ({c.role}): 性格={c.personality[:100]}, 设定={c.forbidden_changes[:100]}" for c in characters])
    
    template = Template(template_text)
    system_prompt = template.render(
        worldview=bible.worldview if bible else "",
        main_conflict=bible.main_conflict if bible else "",
        rules=bible.rules if bible else "",
        characters=chars_text,
        chapter_title=chapter.title,
        chapter_content=version.content
    )
    
    job = gs.create_job(db, project_id, chapter_id, "check_consistency")
    gs.start_job(db, job.id)
    
    try:
        result = client.generate_json(system_prompt, "请检查本章是否存在一致性问题。")
        gs.complete_job(db, job.id, json.dumps(result, ensure_ascii=False, indent=2))
        return result
    except Exception as e:
        gs.fail_job(db, job.id, str(e))
        raise