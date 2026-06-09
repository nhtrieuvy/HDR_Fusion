from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import User


def ensure_user(db: Session, user_id: str, display_name: str | None = None) -> User:
    user = db.get(User, user_id)
    if user is not None:
        return user

    user = User(id=user_id, display_name=display_name or user_id)
    db.add(user)
    db.flush()
    return user
