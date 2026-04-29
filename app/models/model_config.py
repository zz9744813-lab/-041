import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Float, Boolean
from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class ModelConfig(Base):
    __tablename__ = "model_configs"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    provider = Column(String(100), default="")
    base_url = Column(String(500), default="")
    api_key = Column(String(500), default="")
    model = Column(String(255), nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)