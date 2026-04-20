import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.domains.users.models import User
from backend.app.domains.users.models import RefreshToken
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError


def create_user(db: Session, email: str, password: str, full_name: str = None) -> User:
    if db.query(User).filter(User.email == email).first():
        raise ConflictError("Email already registered")
    user = User(email=email, password=hash_password(password), full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user or not verify_password(password, user.password):
        raise UnauthorizedError("Invalid credentials")
    return user


def issue_tokens(db: Session, user: User) -> dict:
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    token_hash = hashlib.sha256(refresh.encode()).hexdigest()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    from app.core.security import decode_token
    from jose import JWTError

    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise UnauthorizedError("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")

    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    stored = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
    ).first()

    if not stored:
        raise UnauthorizedError("Refresh token revoked or not found")

    stored.revoked = True
    db.commit()

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found")

    return issue_tokens(db, user)


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).update({"revoked": True})
    db.commit()