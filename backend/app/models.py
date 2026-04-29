import uuid
from datetime import datetime, date

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    idea = Column(Text, nullable=True, default="")              # 一句话创意
    genre = Column(String(50), nullable=True, default="")       # 题材
    style = Column(String(50), nullable=True, default="")       # 风格
    target_words = Column(Integer, nullable=False, default=50000)  # 目标字数
    status = Column(String(20), nullable=False, default="idea")  # idea/setting_generated/outline_generated/generating/paused/completed/failed
    type = Column(String(20), nullable=False, default="novel")  # novel/short/essay
    word_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    world_items = relationship("WorldItem", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    writing_sessions = relationship("WritingSession", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    story_bible = relationship("StoryBible", back_populates="project", uselist=False, cascade="all, delete-orphan")
    volumes = relationship("Volume", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    memory_entries = relationship("MemoryEntry", back_populates="project", cascade="all, delete-orphan", lazy="selectin")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    volume_id = Column(String(36), ForeignKey("volumes.id"), nullable=True)
    title = Column(String(255), nullable=False)
    chapter_number = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="planned")  # planned/generating/generated/reviewing/approved/failed
    word_count = Column(Integer, nullable=False, default=0)
    outline = Column(Text, nullable=True, default="")           # 章节大纲
    summary = Column(Text, nullable=True, default="")           # 章节摘要
    current_version_id = Column(String(36), ForeignKey("chapter_versions.id"), nullable=True)
    target_words = Column(Integer, nullable=False, default=2000)
    actual_words = Column(Integer, nullable=False, default=0)
    synopsis = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    pov = Column(String(100), nullable=True)
    characters = Column(Text, nullable=True)  # comma-separated
    locations = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="chapters")
    volume = relationship("Volume", back_populates="chapters")
    versions = relationship("ChapterVersion", back_populates="chapter", cascade="all, delete-orphan", lazy="selectin", foreign_keys="ChapterVersion.chapter_id")
    current_version = relationship("ChapterVersion", foreign_keys=[current_version_id], post_update=True, lazy="joined")


class ChapterVersion(Base):
    __tablename__ = "chapter_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    chapter_id = Column(String(36), ForeignKey("chapters.id"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    content = Column(Text, default="")
    word_count = Column(Integer, default=0)
    source = Column(String(50), default="manual")  # manual/generate/continue/revise
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    chapter = relationship("Chapter", back_populates="versions", foreign_keys=[chapter_id])


class Character(Base):
    __tablename__ = "characters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True)
    personality = Column(Text, nullable=True)
    background = Column(Text, nullable=True)
    appearance = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="characters")


class WorldItem(Base):
    __tablename__ = "world_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(20), nullable=False)  # location/timeline/rule/lore
    content = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="world_items")


class WritingSession(Base):
    __tablename__ = "writing_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    word_count = Column(Integer, nullable=False, default=0)
    duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    project = relationship("Project", back_populates="writing_sessions")


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=False)
    model = Column(String(100), nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class StoryBible(Base):
    __tablename__ = "story_bibles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    world_view = Column(Text, default="")
    magic_system = Column(Text, default="")
    main_plot = Column(Text, default="")
    theme = Column(Text, default="")
    tone = Column(Text, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="story_bible")


class Volume(Base):
    __tablename__ = "volumes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    volume_number = Column(Integer, nullable=False, default=1)
    description = Column(Text, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="volumes")
    chapters = relationship("Chapter", back_populates="volume", cascade="all, delete-orphan", lazy="selectin")


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    chapter_id = Column(String(36), ForeignKey("chapters.id"), nullable=True)
    job_type = Column(String(50), nullable=False)  # setting/outline/chapter/continue/revise/consistency
    status = Column(String(20), nullable=False, default="pending")  # pending/running/completed/failed
    progress = Column(Integer, default=0)
    input_snapshot = Column(Text, default="")
    output_text = Column(Text, default="")
    error_message = Column(Text, default="")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ApiUsageLog(Base):
    __tablename__ = "api_usage_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model = Column(String(100), nullable=False)
    job_id = Column(String(36), nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    chapter_id = Column(String(36), nullable=True)
    content = Column(Text, default="")
    entry_type = Column(String(50), default="summary")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    project = relationship("Project", back_populates="memory_entries")