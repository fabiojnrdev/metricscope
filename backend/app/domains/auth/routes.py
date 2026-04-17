from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.domains.auth import service
from app.core.security import create_token

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(data: dict, db: Session = Depends(get_db)):
    user = service.create_user(db, data["email"], data["password"])
    return {"id": user.id}

@router.post("/login")
def login(data: dict, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, data["email"], data["password"])
    if not user:
        return {"error": "invalid credentials"}

    token = create_token({"sub": user.id})
    return {"access_token": token}
def get_current_user(token: str = Depends(create_token), db: Session = Depends(get_db)):
    user_id = service.get_current_user(token)
    if user_id is None:
        return {"error": "invalid token"}
    user = db.query(service.User).filter(service.User.id == user_id).first()
    