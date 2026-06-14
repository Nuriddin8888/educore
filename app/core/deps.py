from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer
from fastapi import Depends, HTTPException

from app.models.user import User
from app.core.config import settings
from app.db.session import SessionLocal

from app.models.student import Student
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


# 🔌 DB ulanish
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token=Depends(security),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # faqat access token
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )

        # faqat User token
        if payload.get("user_type") != "user":
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        user_id = int(payload.get("sub"))

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    payload = decode_token(token)

    # faqat access token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type"
        )

    # faqat student token
    if payload.get("user_type") != "student":
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if payload.get("role") != "student":
        raise HTTPException(
            status_code=403,
            detail="Not student"
        )

    student_id = int(payload.get("sub"))

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student

# 🔥 ROLE CHECK
def require_role(*roles):
    def role_checker(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission"
            )

        return current_user

    return role_checker



