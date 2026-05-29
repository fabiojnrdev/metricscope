from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domains.users.models import User


def get_user_by_email(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise NotFoundError("User")
    return user


def get_active_user_by_email(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user:
        raise NotFoundError("Active user")
    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User")
    return user


__all__ = ["get_user_by_email", "get_active_user_by_email", "get_user_by_id"]
