import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Float
from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class MemoryEntry(Base):
    __tablename__ = "memory_entries"
    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, nullable=False, index=True)
    chapter_id = Column(String, default="", index=True)
    type = Column(String(50), default="")
    title = Column(String(255), default="")
    content = Column(Text, default="")
    embedding_id = Column(String, default="")
    importance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)