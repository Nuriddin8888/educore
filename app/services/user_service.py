from app.models.user import User
from app.core.security import hash_password, verify_password
from sqlalchemy.orm import Session

def create_user(db: Session, data):
    hashed = hash_password(data.password)
    user = User(
        full_name=data.full_name,
        phone_number=data.phone_number,
        email=data.email if data.email else None,
        password=hashed,
        role=data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, phone_number: str, password: str):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user