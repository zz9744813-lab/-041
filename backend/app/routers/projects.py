from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.get("/projects", response_model=List[schemas.ProjectListResponse])
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).order_by(models.Project.updated_at.desc()).all()
    result = []
    for project in projects:
        chapter_count = db.query(func.count(models.Chapter.id)).filter(models.Chapter.project_id == project.id).scalar() or 0
        result.append(schemas.ProjectListResponse(
            id=project.id,
            title=project.title,
            description=project.description or "",
            status=project.status or "active",
            type=project.type or "novel",
            word_count=project.word_count or 0,
            chapter_count=chapter_count,
            created_at=project.created_at,
            updated_at=project.updated_at
        ))
    return result

@router.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/projects", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(
        title=project.title,
        description=project.description,
        status=project.status or "active",
        type=project.type or "novel"
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.put("/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project(project_id: str, project_update: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete dependent records
    db.query(models.Chapter).filter(models.Chapter.project_id == project_id).delete()
    db.query(models.Character).filter(models.Character.project_id == project_id).delete()
    db.query(models.WorldItem).filter(models.WorldItem.project_id == project_id).delete()
    
    db.delete(db_project)
    db.commit()
    return {"message": "Project deleted"}