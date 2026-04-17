from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

SECRET = "supersecret"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)

def create_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=2)
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)
def decode_token(token: str):
    payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    payload.pop("exp", None)
    return payload
def get_current_user(token: str):
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except Exception:
        return None
