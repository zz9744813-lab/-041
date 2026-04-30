from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import export_service

router = APIRouter()

@router.get("/projects/{project_id}/export/txt")
def export_txt(project_id: str, db: Session = Depends(get_db)):
    filepath, filename = export_service.export_txt(db, project_id)
    return FileResponse(filepath, media_type="text/plain", filename=filename)

@router.get("/projects/{project_id}/export/md")
def export_md(project_id: str, db: Session = Depends(get_db)):
    filepath, filename = export_service.export_markdown(db, project_id)
    return FileResponse(filepath, media_type="text/markdown", filename=filename)
