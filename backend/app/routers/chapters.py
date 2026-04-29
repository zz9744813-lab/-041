from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app import models, schemas
from app.utils import file_storage

router = APIRouter()

@router.get("/projects/{project_id}/chapters", response_model=List[schemas.ChapterResponse])
def get_chapters(project_id: str, db: Session = Depends(get_db)):
    chapters = db.query(models.Chapter).filter(models.Chapter.project_id == project_id).order_by(models.Chapter.chapter_number).all()
    for chapter in chapters:
        chapter.content = ""  # Hide content in list view
    return chapters

@router.get("/projects/{project_id}/chapters/{chapter_id}", response_model=schemas.ChapterDetailResponse)
def get_chapter(project_id: str, chapter_id: str, db: Session = Depends(get_db)):
    chapter = db.query(models.Chapter).filter(models.Chapter.id == chapter_id, models.Chapter.project_id == project_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    # Load content from file
    chapter.content = file_storage.read_chapter(project_id, chapter_id) or ""
    return chapter

@router.post("/projects/{project_id}/chapters", response_model=schemas.ChapterDetailResponse)
def create_chapter(project_id: str, chapter: schemas.ChapterCreate, db: Session = Depends(get_db)):
    # Get next chapter number
    max_number = db.query(models.Chapter.chapter_number).filter(models.Chapter.project_id == project_id).order_by(models.Chapter.chapter_number.desc()).first()
    next_number = (max_number[0] + 1) if max_number else 1
    
    db_chapter = models.Chapter(
        project_id=project_id,
        title=chapter.title,
        synopsis=chapter.synopsis,
        notes=chapter.notes,
        pov=chapter.pov,
        characters=chapter.characters,
        locations=chapter.locations,
        chapter_number=next_number,
        status=chapter.status or "draft",
        word_count=len((chapter.content or "").split())
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    
    # Save content to file
    if chapter.content:
        file_storage.write_chapter(project_id, db_chapter.id, chapter.content)
    
    db_chapter.content = chapter.content or ""
    return db_chapter

@router.put("/projects/{project_id}/chapters/{chapter_id}", response_model=schemas.ChapterDetailResponse)
def update_chapter(project_id: str, chapter_id: str, chapter_update: schemas.ChapterUpdate, db: Session = Depends(get_db)):
    db_chapter = db.query(models.Chapter).filter(models.Chapter.id == chapter_id, models.Chapter.project_id == project_id).first()
    if not db_chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    update_data = chapter_update.model_dump(exclude_unset=True)
    
    # Check if we need to read content for word count recalculation
    content_changed = "content" in update_data
    if content_changed:
        file_storage.write_chapter(project_id, chapter_id, update_data["content"])
        update_data["word_count"] = len(update_data["content"].split()) if update_data["content"] else 0
    elif "word_count" not in update_data:
        update_data["word_count"] = len(file_storage.read_chapter(project_id, chapter_id) or "")
    
    for field, value in update_data.items():
        if field != "content":
            setattr(db_chapter, field, value)
    
    db.commit()
    db.refresh(db_chapter)
    
    # Return with content
    if content_changed:
        db_chapter.content = update_data["content"]
    else:
        db_chapter.content = file_storage.read_chapter(project_id, chapter_id) or ""
    
    return db_chapter

@router.delete("/projects/{project_id}/chapters/{chapter_id}")
def delete_chapter(project_id: str, chapter_id: str, db: Session = Depends(get_db)):
    db_chapter = db.query(models.Chapter).filter(models.Chapter.id == chapter_id, models.Chapter.project_id == project_id).first()
    if not db_chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Delete file
    file_storage.delete_chapter_file(project_id, chapter_id)
    
    # Delete from DB
    db.delete(db_chapter)
    db.commit()
    return {"message": "Chapter deleted"}

@router.put("/projects/{project_id}/chapters/{chapter_id}/reorder")
def reorder_chapter(project_id: str, chapter_id: str, reorder: schemas.ChapterReorder, db: Session = Depends(get_db)):
    db_chapter = db.query(models.Chapter).filter(models.Chapter.id == chapter_id, models.Chapter.project_id == project_id).first()
    if not db_chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # If moving down, chapters between old and new positions need their numbers adjusted
    old_number = db_chapter.chapter_number
    new_number = reorder.chapter_number
    
    if old_number == new_number:
        return {"message": "No change"}
    
    if new_number < old_number:  # Moving up
        db.query(models.Chapter).filter(
            models.Chapter.project_id == project_id,
            models.Chapter.chapter_number >= new_number,
            models.Chapter.chapter_number < old_number,
            models.Chapter.id != chapter_id
        ).update({models.Chapter.chapter_number: models.Chapter.chapter_number + 1})
    else:  # Moving down
        db.query(models.Chapter).filter(
            models.Chapter.project_id == project_id,
            models.Chapter.chapter_number > old_number,
            models.Chapter.chapter_number <= new_number,
            models.Chapter.id != chapter_id
        ).update({models.Chapter.chapter_number: models.Chapter.chapter_number - 1})
    
    db_chapter.chapter_number = new_number
    db.commit()
    return {"message": "Chapter reordered"}