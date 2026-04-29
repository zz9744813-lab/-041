from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


# ─── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    idea: Optional[str] = ""
    genre: Optional[str] = ""
    style: Optional[str] = ""
    target_words: Optional[int] = 50000
    type: Optional[str] = "novel"
    status: Optional[str] = "idea"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    idea: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    target_words: Optional[int] = None
    type: Optional[str] = None
    status: Optional[str] = None
    word_count: Optional[int] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    idea: Optional[str] = ""
    genre: Optional[str] = ""
    style: Optional[str] = ""
    target_words: int = 50000
    status: str = "idea"
    type: str = "novel"
    word_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    status: str = "idea"
    type: str = "novel"
    word_count: int = 0
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
    status: Optional[str] = "planned"
    outline: Optional[str] = ""
    target_words: Optional[int] = 2000
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
    outline: Optional[str] = None
    summary: Optional[str] = None
    target_words: Optional[int] = None
    actual_words: Optional[int] = None
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
    volume_id: Optional[str] = None
    title: str
    chapter_number: int
    status: str = "planned"
    word_count: int = 0
    outline: Optional[str] = ""
    summary: Optional[str] = ""
    current_version_id: Optional[str] = None
    target_words: int = 2000
    actual_words: int = 0
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


# ─── ChapterVersion ────────────────────────────────────────────────────────────

class ChapterVersionResponse(BaseModel):
    id: str
    chapter_id: str
    version_number: int
    content: str = ""
    word_count: int = 0
    source: str = "manual"
    created_at: datetime

    class Config:
        from_attributes = True


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


# ─── Stats / Overview ──────────────────────────────────────────────────────────

class OverviewResponse(BaseModel):
    total_projects: int = 0
    total_word_count: int = 0
    total_chapters: int = 0


class DailyStatsResponse(BaseModel):
    date: date
    word_count: int
    duration_minutes: Optional[int] = None


# ─── ModelConfig ───────────────────────────────────────────────────────────────

class ModelConfigCreate(BaseModel):
    name: str
    base_url: str
    api_key: str
    model: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    is_default: Optional[bool] = False


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = None


class ModelConfigResponse(BaseModel):
    id: str
    name: str
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── StoryBible ────────────────────────────────────────────────────────────────

class StoryBibleResponse(BaseModel):
    id: str
    project_id: str
    world_view: str = ""
    magic_system: str = ""
    main_plot: str = ""
    theme: str = ""
    tone: str = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Volume ────────────────────────────────────────────────────────────────────

class VolumeCreate(BaseModel):
    title: str
    volume_number: Optional[int] = 1
    description: Optional[str] = ""


class VolumeResponse(BaseModel):
    id: str
    project_id: str
    title: str
    volume_number: int
    description: str = ""
    created_at: datetime
    updated_at: datetime
    chapter_count: int = 0

    class Config:
        from_attributes = True


# ─── GenerationJob ─────────────────────────────────────────────────────────────

class GenerationJobResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    chapter_id: Optional[str] = None
    job_type: str
    status: str = "pending"
    progress: int = 0
    input_snapshot: str = ""
    output_text: str = ""
    error_message: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── ApiUsageLog ───────────────────────────────────────────────────────────────

class ApiUsageLogResponse(BaseModel):
    id: str
    model: str
    job_id: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    success: bool = True
    error_message: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


# ─── MemoryEntry ───────────────────────────────────────────────────────────────

class MemoryEntryResponse(BaseModel):
    id: str
    project_id: str
    chapter_id: Optional[str] = None
    content: str = ""
    entry_type: str = "summary"
    created_at: datetime

    class Config:
        from_attributes = True