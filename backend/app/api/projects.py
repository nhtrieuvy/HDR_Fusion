from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.project_service import create_project, list_projects

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead)
def post_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return create_project(db, payload)


@router.get("", response_model=list[ProjectRead])
def get_projects(user_id: str | None = Query(default=None), db: Session = Depends(get_db)):
    return list_projects(db, user_id=user_id)

