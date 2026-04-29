from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.chapter import Chapter
from app.services import chapter_service, consistency_service

router = APIRouter()

@router.post("/projects/{project_id}/chapters/{chapter_id}/generate")
def gen_chapter(project_id: str, chapter_id: str, db: Session = Depends(get_db)):
    try:
        chapter_service.generate_chapter(db, project_id, chapter_id)
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}?error={str(e)}", status_code=303)

@router.post("/projects/{project_id}/chapters/{chapter_id}/revise")
def revise_chapter(project_id: str, chapter_id: str, db: Session = Depends(get_db)):
    try:
        chapter_service.revise_chapter(db, project_id, chapter_id)
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}?error={str(e)}", status_code=303)

@router.post("/projects/{project_id}/chapters/{chapter_id}/check-consistency")
def check_consistency(project_id: str, chapter_id: str, db: Session = Depends(get_db)):
    try:
        result = consistency_service.check_consistency(db, project_id, chapter_id)
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}?error={str(e)}", status_code=303)

@router.post("/projects/{project_id}/chapters/{chapter_id}/edit")
def edit_chapter(project_id: str, chapter_id: str, content: str = Form(""), db: Session = Depends(get_db)):
    try:
        chapter_service.save_manual_version(db, chapter_id, content)
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}?error={str(e)}", status_code=303)

@router.post("/projects/{project_id}/chapters/{chapter_id}/switch-version/{version_id}")
def switch_version(project_id: str, chapter_id: str, version_id: str, db: Session = Depends(get_db)):
    try:
        chapter_service.switch_version(db, chapter_id, version_id)
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/projects/{project_id}/chapters/{chapter_id}?error={str(e)}", status_code=303)
