from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.memory import MemoryEntry
from datetime import datetime

def add_memory_entry(db: Session, project_id: str, chapter_id: Optional[str], type: str, title: str, content: str, importance: int = 5) -> MemoryEntry:
    entry = MemoryEntry(
        project_id=project_id,
        chapter_id=chapter_id,
        type=type,
        title=title,
        content=content,
        importance=importance
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_memories(db: Session, project_id: str, limit: int = 50) -> List[MemoryEntry]:
    return db.query(MemoryEntry).filter(
        MemoryEntry.project_id == project_id
    ).order_by(MemoryEntry.created_at.desc()).limit(limit).all()
