from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChapterResponse(BaseModel):
    id: str
    project_id: str
    volume_id: Optional[str] = None
    chapter_number: int
    title: Optional[str] = None
    outline: Optional[str] = None
    summary: Optional[str] = None
    current_version_id: Optional[str] = None
    status: Optional[str] = None
    target_words: Optional[int] = None
    actual_words: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChapterVersionResponse(BaseModel):
    id: str
    chapter_id: str
    version_number: int
    content: Optional[str] = None
    source: Optional[str] = None
    model_config_id: Optional[str] = None
    prompt_version: Optional[str] = None
    word_count: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChapterUpdateRequest(BaseModel):
    title: Optional[str] = None
    outline: Optional[str] = None