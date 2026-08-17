from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models import Role, TripMember, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user_id = decode_access_token(token)
    user = db.get(User, user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida ou expirada")
    return user

def trip_member(trip_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TripMember:
    member = db.query(TripMember).filter_by(trip_id=trip_id, user_id=user.id).first()
    if not member:
        raise HTTPException(status_code=403, detail="Você não participa desta viagem")
    return member

def trip_manager(member: TripMember = Depends(trip_member)) -> TripMember:
    if member.role not in (Role.ADMIN, Role.ORGANIZER):
        raise HTTPException(status_code=403, detail="Ação restrita a administradores e organizadores")
    return member

