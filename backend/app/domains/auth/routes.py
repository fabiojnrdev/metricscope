from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.auth import service
from app.domains.auth.schemas import (
    RegisterRequest, LoginRequest, RefreshRequest,
    TokenResponse, UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = service.create_user(db, data.email, data.password, data.full_name)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, data.email, data.password)
    return service.issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return service.refresh_access_token(db, data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    service.revoke_refresh_token(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user