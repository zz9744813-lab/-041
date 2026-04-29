from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


# ─── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    status: Optional[str] = "active"
    type: Optional[str] = "novel"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    word_count: Optional[int] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    status: str
    type: str
    word_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    status: str
    type: str
    word_count: int
    chapter_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectStatsResponse(BaseModel):
    id: str
    title: str
    total_word_count: int = 0
    chapter_count: int = 0
    character_count: int = 0


# ─── Chapter ───────────────────────────────────────────────────────────────────

class ChapterCreate(BaseModel):
    title: str
    status: Optional[str] = "draft"
    synopsis: Optional[str] = None
    notes: Optional[str] = None
    pov: Optional[str] = None
    characters: Optional[str] = None
    locations: Optional[str] = None
    content: Optional[str] = ""


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    chapter_number: Optional[int] = None
    word_count: Optional[int] = None
    synopsis: Optional[str] = None
    notes: Optional[str] = None
    pov: Optional[str] = None
    characters: Optional[str] = None
    locations: Optional[str] = None
    content: Optional[str] = None


class ChapterReorder(BaseModel):
    chapter_number: int


class ChapterResponse(BaseModel):
    id: str
    project_id: str
    title: str
    chapter_number: int
    status: str
    word_count: int
    synopsis: Optional[str] = None
    notes: Optional[str] = None
    pov: Optional[str] = None
    characters: Optional[str] = None
    locations: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChapterDetailResponse(ChapterResponse):
    content: str = ""


# ─── Character ─────────────────────────────────────────────────────────────────

class CharacterCreate(BaseModel):
    name: str
    age: Optional[str] = None
    gender: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    appearance: Optional[str] = None
    notes: Optional[str] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    appearance: Optional[str] = None
    notes: Optional[str] = None


class CharacterResponse(BaseModel):
    id: str
    project_id: str
    name: str
    age: Optional[str] = None
    gender: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    appearance: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── WorldItem ─────────────────────────────────────────────────────────────────

class WorldItemCreate(BaseModel):
    title: str
    category: str  # location/timeline/rule/lore
    content: Optional[str] = ""


class WorldItemUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None


class WorldItemResponse(BaseModel):
    id: str
    project_id: str
    title: str
    category: str
    content: Optional[str] = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── WritingSession ────────────────────────────────────────────────────────────

class WritingSessionCreate(BaseModel):
    date: Optional[date] = None
    word_count: int = 0
    duration_minutes: Optional[int] = None


class WritingSessionUpdate(BaseModel):
    date: Optional[date] = None
    word_count: Optional[int] = None
    duration_minutes: Optional[int] = None


class WritingSessionResponse(BaseModel):
    id: str
    project_id: str
    date: date
    word_count: int
    duration_minutes: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DailyStatsResponse(BaseModel):
    date: date
    word_count: int
    duration_minutes: Optional[int] = None


# ─── Stats / Overview ──────────────────────────────────────────────────────────

class OverviewResponse(BaseModel):
    total_projects: int = 0
    total_word_count: int = 0
    total_chapters: int = 0