import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Float, Boolean
from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class ApiUsageLog(Base):
    __tablename__ = "api_usage_logs"
    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, default="", index=True)
    job_id = Column(String, default="", index=True)
    model = Column(String(255), default="")
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)