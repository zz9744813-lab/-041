import logging
from typing import List
from sqlalchemy.orm import Session
from app.models import MemoryEntry

logger = logging.getLogger(__name__)


def get_recent_memories(project_id: str, db: Session, limit: int = 10) -> List[MemoryEntry]:
    return db.query(MemoryEntry).filter(
        MemoryEntry.project_id == project_id
    ).order_by(MemoryEntry.created_at.desc()).limit(limit).all()


def add_memory(project_id: str, content: str, entry_type: str,
               chapter_id: str = None, db: Session = None) -> MemoryEntry:
    entry = MemoryEntry(
        project_id=project_id,
        chapter_id=chapter_id,
        content=content,
        entry_type=entry_type
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def clear_project_memories(project_id: str, db: Session) -> None:
    db.query(MemoryEntry).filter(MemoryEntry.project_id == project_id).delete()
    db.commit()
