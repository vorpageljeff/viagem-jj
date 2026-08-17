from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return password_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_context.verify(password, hashed)

def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> int | None:
    try:
        return int(jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])["sub"])
    except (JWTError, KeyError, ValueError):
        return None

