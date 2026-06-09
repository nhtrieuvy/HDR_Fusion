from app.db.models import User
from app.db.session import SessionLocal, init_database
from app.schemas.project import ProjectCreate
from app.services.project_service import create_project


def test_create_project_ensures_local_user():
    init_database()

    with SessionLocal() as db:
        project = create_project(db, ProjectCreate(name="local project", user_id="local"))

        assert project.user_id == "local"
        assert db.get(User, "local") is not None
