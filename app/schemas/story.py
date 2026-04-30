from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class StoryBibleResponse(BaseModel):
    id: str
    project_id: str
    worldview: Optional[str] = None
    main_conflict: Optional[str] = None
    theme: Optional[str] = None
    tone: Optional[str] = None
    writing_style: Optional[str] = None
    rules: Optional[str] = None
    raw_json: Optional[Any] = None

    model_config = {"from_attributes": True}


class CharacterResponse(BaseModel):
    id: str
    project_id: str
    name: str
    role: Optional[str] = None
    age: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    goal: Optional[str] = None
    background: Optional[str] = None
    relationships: Optional[str] = None
    abilities: Optional[str] = None
    forbidden_changes: Optional[str] = None

    model_config = {"from_attributes": True}


class VolumeResponse(BaseModel):
    id: str
    project_id: str
    volume_number: int
    title: Optional[str] = None
    summary: Optional[str] = None
    target_words: Optional[int] = None
    status: Optional[str] = None
    chapter_count: int = 0

    model_config = {"from_attributes": True}