import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime
from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class StoryBible(Base):
    __tablename__ = "story_bibles"
    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, nullable=False, index=True)
    worldview = Column(Text, default="")
    main_conflict = Column(Text, default="")
    theme = Column(Text, default="")
    tone = Column(Text, default="")
    writing_style = Column(Text, default="")
    rules = Column(Text, default="")
    raw_json = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Character(Base):
    __tablename__ = "characters"
    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100), default="")
    age = Column(String(50), default="")
    appearance = Column(Text, default="")
    personality = Column(Text, default="")
    goal = Column(Text, default="")
    background = Column(Text, default="")
    relationships = Column(Text, default="")
    abilities = Column(Text, default="")
    forbidden_changes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Volume(Base):
    __tablename__ = "volumes"
    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, nullable=False, index=True)
    volume_number = Column(Integer, default=0)
    title = Column(String(255), default="")
    summary = Column(Text, default="")
    target_words = Column(Integer, default=0)
    status = Column(String(50), default="planning")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)