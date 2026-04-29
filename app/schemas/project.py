from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str
    idea: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    target_words: Optional[int] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    idea: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    target_words: Optional[int] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    idea: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    target_words: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    id: str
    title: str
    idea: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    target_words: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    chapter_count: int = 0
    total_words: int = 0

    model_config = {"from_attributes": True}