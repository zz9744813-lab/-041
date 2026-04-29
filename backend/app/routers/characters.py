from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.get("/projects/{project_id}/characters", response_model=List[schemas.CharacterResponse])
def get_characters(project_id: str, db: Session = Depends(get_db)):
    characters = db.query(models.Character).filter(models.Character.project_id == project_id).order_by(models.Character.name).all()
    return characters

@router.post("/projects/{project_id}/characters", response_model=schemas.CharacterResponse)
def create_character(project_id: str, character: schemas.CharacterCreate, db: Session = Depends(get_db)):
    db_check_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_check_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_character = models.Character(
        project_id=project_id,
        name=character.name,
        age=character.age,
        gender=character.gender,
        personality=character.personality,
        background=character.background,
        appearance=character.appearance,
        notes=character.notes
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character

@router.put("/projects/{project_id}/characters/{character_id}", response_model=schemas.CharacterResponse)
def update_character(project_id: str, character_id: str, character_update: schemas.CharacterUpdate, db: Session = Depends(get_db)):
    db_character = db.query(models.Character).filter(models.Character.id == character_id, models.Character.project_id == project_id).first()
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    update_data = character_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_character, field, value)
    
    db.commit()
    db.refresh(db_character)
    return db_character

@router.delete("/projects/{project_id}/characters/{character_id}")
def delete_character(project_id: str, character_id: str, db: Session = Depends(get_db)):
    db_character = db.query(models.Character).filter(models.Character.id == character_id, models.Character.project_id == project_id).first()
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    db.delete(db_character)
    db.commit()
    return {"message": "Character deleted"}