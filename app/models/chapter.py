import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime
from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, nullable=False, index=True)
    volume_id = Column(String, nullable=False, index=True)
    chapter_number = Column(Integer, default=0)
    title = Column(String(255), default="")
    outline = Column(Text, default="")
    summary = Column(Text, default="")
    current_version_id = Column(String, default="")
    status = Column(String(50), default="draft")
    target_words = Column(Integer, default=0)
    actual_words = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChapterVersion(Base):
    __tablename__ = "chapter_versions"
    id = Column(String, primary_key=True, default=gen_uuid)
    chapter_id = Column(String, nullable=False, index=True)
    version_number = Column(Integer, default=1)
    content = Column(Text, default="")
    source = Column(String(100), default="")
    model_config_id = Column(String, default="")
    prompt_version = Column(String(50), default="")
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)