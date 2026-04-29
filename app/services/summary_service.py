import json, logging, os
from sqlalchemy.orm import Session
from jinja2 import Template
from app.models.story import StoryBible, Character
from app.models.chapter import Chapter, ChapterVersion
from app.services.llm_client import LLMClient
from app.services import generation_service as gs
from app.services import memory_service as ms

logger = logging.getLogger(__name__)

def extract_summary(db: Session, project_id: str, chapter_id: str) -> dict:
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter or not chapter.current_version_id:
        raise ValueError("Chapter has no content to summarize")
    
    version = db.query(ChapterVersion).filter(ChapterVersion.id == chapter.current_version_id).first()
    if not version:
        raise ValueError("Version not found")
    
    client = LLMClient.get_default_client(db)
    
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "summary_extractor.md")
    with open(prompt_path, "r") as f:
        template_text = f.read()
    
    template = Template(template_text)
    system_prompt = template.render(
        chapter_title=chapter.title,
        chapter_content=version.content
    )
    
    job = gs.create_job(db, project_id, chapter_id, "summarize_chapter")
    gs.start_job(db, job.id)
    
    try:
        result = client.generate_json(system_prompt, "请提取本章摘要。")
        
        chapter.summary = result.get("chapter_summary", "")
        db.commit()
        
        # Save memory entries
        for event in result.get("key_events", []):
            ms.add_memory_entry(db, project_id, chapter_id, "event", f"第{chapter.chapter_number}章事件", event, importance=7)
        for change in result.get("character_changes", []):
            ms.add_memory_entry(db, project_id, chapter_id, "relationship_change", "角色变化", change, importance=6)
        for fact in result.get("world_facts", []):
            ms.add_memory_entry(db, project_id, chapter_id, "world_fact", "世界观补充", fact, importance=5)
        for fh in result.get("foreshadowing", []):
            ms.add_memory_entry(db, project_id, chapter_id, "foreshadowing", "伏笔", fh, importance=8)
        
        gs.complete_job(db, job.id, json.dumps(result, ensure_ascii=False, indent=2))
        return result
        
    except Exception as e:
        gs.fail_job(db, job.id, str(e))
        raise