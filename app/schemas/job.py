from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    project_id: str
    chapter_id: Optional[str] = None
    job_type: str
    status: str
    progress: float = 0.0
    input_snapshot: Optional[Any] = None
    output_text: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    id: str
    project_id: str
    chapter_id: Optional[str] = None
    job_type: str
    status: str
    progress: float = 0.0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}