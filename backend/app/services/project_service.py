from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Project
from app.schemas.project import ProjectCreate
from app.services.user_service import ensure_user


def create_project(db: Session, payload: ProjectCreate) -> Project:
    if payload.user_id:
        ensure_user(db, payload.user_id)
    project = Project(name=payload.name, description=payload.description, user_id=payload.user_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, user_id: str | None = None) -> list[Project]:
    statement = select(Project).order_by(Project.created_at.desc())
    if user_id:
        statement = statement.where(Project.user_id == user_id)
    return list(db.scalars(statement))
