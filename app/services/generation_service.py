import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.job import GenerationJob
import json

logger = logging.getLogger(__name__)

def create_job(db: Session, project_id: str, chapter_id: Optional[str], job_type: str) -> GenerationJob:
    job = GenerationJob(
        project_id=project_id,
        chapter_id=chapter_id,
        job_type=job_type,
        status="pending",
        progress=0.0
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def start_job(db: Session, job_id: str):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if job:
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

def update_job_progress(db: Session, job_id: str, progress: float):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if job:
        job.progress = progress
        db.commit()

def complete_job(db: Session, job_id: str, output_text: str):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if job:
        job.status = "success"
        job.progress = 100.0
        job.output_text = output_text
        job.finished_at = datetime.utcnow()
        db.commit()

def fail_job(db: Session, job_id: str, error_message: str):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if job:
        job.status = "failed"
        job.error_message = error_message
        job.finished_at = datetime.utcnow()
        db.commit()

def cancel_job(db: Session, job_id: str):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if job:
        job.status = "cancelled"
        job.finished_at = datetime.utcnow()
        db.commit()

def reset_stale_jobs(db: Session):
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    stale = db.query(GenerationJob).filter(
        GenerationJob.status == "running",
        GenerationJob.started_at < cutoff
    ).all()
    for job in stale:
        job.status = "failed"
        job.error_message = "Stale job - service restarted or timed out"
        job.finished_at = datetime.utcnow()
    if stale:
        db.commit()
        logger.info(f"Reset {len(stale)} stale jobs")
