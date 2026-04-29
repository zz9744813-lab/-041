from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.get("/projects/{project_id}/world", response_model=List[schemas.WorldItemResponse])
def get_world_items(project_id: str, db: Session = Depends(get_db)):
    items = db.query(models.WorldItem).filter(models.WorldItem.project_id == project_id).order_by(models.WorldItem.category, models.WorldItem.title).all()
    return items

@router.post("/projects/{project_id}/world", response_model=schemas.WorldItemResponse)
def create_world_item(project_id: str, world_item: schemas.WorldItemCreate, db: Session = Depends(get_db)):
    db_check_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_check_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_item = models.WorldItem(
        project_id=project_id,
        title=world_item.title,
        category=world_item.category,
        content=world_item.content or ""
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/projects/{project_id}/world/{world_id}", response_model=schemas.WorldItemResponse)
def update_world_item(project_id: str, world_id: str, world_update: schemas.WorldItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.WorldItem).filter(models.WorldItem.id == world_id, models.WorldItem.project_id == project_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="World item not found")
    
    update_data = world_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/projects/{project_id}/world/{world_id}")
def delete_world_item(project_id: str, world_id: str, db: Session = Depends(get_db)):
    db_item = db.query(models.WorldItem).filter(models.WorldItem.id == world_id, models.WorldItem.project_id == project_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="World item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "World item deleted"}