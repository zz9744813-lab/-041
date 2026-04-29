from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import GenerationJob
from app.schemas import GenerationJobResponse

router = APIRouter()


@router.get("/projects/{project_id}/jobs", response_model=List[GenerationJobResponse])
def get_project_jobs(project_id: str, db: Session = Depends(get_db)):
    jobs = db.query(GenerationJob).filter(
        GenerationJob.project_id == project_id
    ).order_by(GenerationJob.created_at.desc()).limit(50).all()
    return jobs


@router.get("/chapters/{chapter_id}/jobs", response_model=List[GenerationJobResponse])
def get_chapter_jobs(chapter_id: str, db: Session = Depends(get_db)):
    jobs = db.query(GenerationJob).filter(
        GenerationJob.chapter_id == chapter_id
    ).order_by(GenerationJob.created_at.desc()).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=GenerationJobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs", response_model=List[GenerationJobResponse])
def get_all_jobs(limit: int = 20, db: Session = Depends(get_db)):
    jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).limit(limit).all()
    return jobs


@router.post("/jobs/{job_id}/retry", response_model=GenerationJobResponse)
def retry_job(job_id: str, db: Session = Depends(get_db)):
    from datetime import datetime
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "failed":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    # Re-run the appropriate service based on job type
    try:
        if job.job_type == "setting":
            from app.services.setting_service import generate_setting
            new_job = generate_setting(job.project_id, db)
        elif job.job_type == "outline":
            from app.services.outline_service import generate_outline
            new_job = generate_outline(job.project_id, db)
        elif job.job_type == "chapter":
            from app.services.chapter_service import generate_chapter
            new_job = generate_chapter(job.chapter_id, db)
        elif job.job_type == "continue":
            from app.services.chapter_service import continue_chapter
            new_job = continue_chapter(job.chapter_id, "", db)
        elif job.job_type == "revise":
            from app.services.chapter_service import revise_chapter
            new_job = revise_chapter(job.chapter_id, "", db)
        elif job.job_type == "consistency":
            from app.services.consistency_service import check_consistency
            new_job = check_consistency(job.chapter_id, db)
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Cannot retry job type: {job.job_type}")
        return new_job
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    from datetime import datetime
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "running":
        job.status = "failed"
        job.error_message = "Cancelled by user"
        job.finished_at = datetime.utcnow()
        db.commit()
    return {"message": "Job cancelled"}
