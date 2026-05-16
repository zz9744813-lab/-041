"""Asset CRUD schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AssetType, Market


class AssetBase(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    market: Market
    asset_type: AssetType
    sector: str | None = None
    is_active: bool = True
    priority: int = 10


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: str | None = None
    sector: str | None = None
    is_active: bool | None = None
    priority: int | None = None


class AssetOut(AssetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
