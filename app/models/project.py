import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime
from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(255), nullable=False)
    idea = Column(Text, default="")
    genre = Column(String(100), default="")
    style = Column(String(100), default="")
    target_words = Column(Integer, default=0)
    status = Column(String(50), default="idea")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)