import uuid
from datetime import datetime, date

from sqlalchemy import Column, String, Text, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import TEXT as SQLITE_TEXT
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    status = Column(String(20), nullable=False, default="active")  # active/archived
    type = Column(String(20), nullable=False, default="novel")  # novel/short/essay
    word_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    world_items = relationship("WorldItem", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    writing_sessions = relationship("WritingSession", back_populates="project", cascade="all, delete-orphan", lazy="selectin")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    chapter_number = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="draft")  # draft/wip/review/done
    word_count = Column(Integer, nullable=False, default=0)
    synopsis = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    pov = Column(String(100), nullable=True)
    characters = Column(Text, nullable=True)  # comma-separated
    locations = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="chapters")


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