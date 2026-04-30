from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import GenerationJob
from app.models.chapter import Chapter
from app.services import generation_service as gs, chapter_service

router = APIRouter()

@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        return RedirectResponse(url="/jobs", status_code=303)
    
    # Reset job
    job.status = "pending"
    job.error_message = ""
    job.progress = 0.0
    db.commit()
    
    # If it's a chapter generation job, reset chapter too
    if job.chapter_id and job.job_type == "generate_chapter":
        chapter = db.query(Chapter).filter(Chapter.id == job.chapter_id).first()
        if chapter:
            chapter.status = "planned"
            db.commit()
    
    return RedirectResponse(url="/jobs", status_code=303)

@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    gs.cancel_job(db, job_id)
    return RedirectResponse(url="/jobs", status_code=303)

@router.get("/jobs/{job_id}/status")
def job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        return JSONResponse({"status": "not_found"})
    return JSONResponse({
        "status": job.status,
        "progress": job.progress,
        "error_message": job.error_message[:200] if job.error_message else None
    })
