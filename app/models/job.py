import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Float
from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, nullable=False, index=True)
    chapter_id = Column(String, default="", index=True)
    job_type = Column(String(50), default="")
    status = Column(String(50), default="pending")
    progress = Column(Integer, default=0)
    input_snapshot = Column(Text, default="")
    output_text = Column(Text, default="")
    error_message = Column(Text, default="")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)