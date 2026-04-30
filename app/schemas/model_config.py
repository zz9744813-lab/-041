from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ModelConfigCreate(BaseModel):
    name: str
    provider: str
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    is_default: bool = False


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = None


class ModelConfigResponse(BaseModel):
    id: str
    name: str
    provider: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    is_default: bool
    api_key_display: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        d = super().from_orm(obj)
        if obj.api_key and len(obj.api_key) > 4:
            d.api_key_display = "..." + obj.api_key[-4:]
        else:
            d.api_key_display = obj.api_key
        return d


class ModelConfigTestRequest(BaseModel):
    base_url: str
    api_key: str
    model: str