from sqlalchemy.orm import Session
from app.domains.auth.models import User
from app.core.security import hash_password, verify_password

def create_user(db: Session, email: str, password: str):
    user = User(email=email, password=hash_password(password))
    db.add(user)
    db.commit()
    return user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user