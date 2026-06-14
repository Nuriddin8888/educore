import os
import uuid
from fastapi import UploadFile, File
from app.core.constants import FACE_SIMILARITY_THRESHOLD
from app.services.face_service import extract_embedding, cosine_similarity


from app.models.user import User
from sqlalchemy.orm import Session
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.deps import get_current_user, get_db
from app.schemas.user import UserCreate, UserLogin
from fastapi import APIRouter, Depends, HTTPException
from app.services.user_service import create_user, authenticate_user


router = APIRouter(prefix="/auth", tags=["Auth"])



@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.phone_number, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role,
            "user_type": "user"
        }
    )

    refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "role": user.role,
            "user_type": "user"
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "role": user.role
        }
    }


@router.post("/refresh")
def refresh_token(refresh_token: str):

    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    new_access_token = create_access_token(
        {
            "sub": payload["sub"],
            "role": payload["role"],
            "user_type": payload["user_type"]
        }
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }



@router.post("/face-login")
def face_login(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    os.makedirs(
        "app/media/temp",
        exist_ok=True
    )

    filename = f"{uuid.uuid4()}.jpg"

    temp_path = (
        f"app/media/temp/{filename}"
    )

    try:

        # Rasmni vaqtinchalik saqlash
        with open(temp_path, "wb") as f:
            f.write(
                file.file.read()
            )

        # Embedding olish
        embedding = extract_embedding(
            temp_path
        )

        if embedding is None:
            raise HTTPException(
                status_code=400,
                detail="Face not detected"
            )

        # Face ID yoqilgan userlarni olish
        users = db.query(User).filter(
            User.face_embedding.isnot(None),
            User.face_enabled == True
        ).all()

        if not users:
            raise HTTPException(
                status_code=404,
                detail="No registered faces found"
            )

        best_user = None
        best_score = 0

        # Eng o'xshash yuzni topish
        for user in users:

            score = cosine_similarity(
                embedding,
                user.face_embedding
            )

            if score > best_score:
                best_score = score
                best_user = user

        # User topilmasa
        if best_user is None:
            raise HTTPException(
                status_code=401,
                detail="Face not recognized"
            )

        # Similarity yetarli bo'lmasa
        if best_score < FACE_SIMILARITY_THRESHOLD:
            raise HTTPException(
                status_code=401,
                detail="Face not recognized"
            )

        # JWT token yaratish
        access_token = create_access_token(
            {
                "sub": str(best_user.id),
                "role": best_user.role,
                "user_type": "user"
            }
        )

        refresh_token = create_refresh_token(
            {
                "sub": str(best_user.id),
                "role": best_user.role,
                "user_type": "user"
            }
        )


        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "similarity": round(best_score, 3),
            "user": {
                "id": best_user.id,
                "full_name": best_user.full_name,
                "phone_number": best_user.phone_number,
                "role": best_user.role
            }
        }

    finally:

        # Temp faylni o'chirish
        if os.path.exists(temp_path):
            os.remove(temp_path)



@router.post("/enable-face-id")
def enable_face_id(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    folder = (
        f"app/media/faces/"
        f"{current_user.role}"
    )

    os.makedirs(
        folder,
        exist_ok=True
    )

    image_path = (
        f"{folder}/"
        f"{current_user.id}.jpg"
    )

    with open(
        image_path,
        "wb"
    ) as f:

        f.write(
            file.file.read()
        )

    embedding = extract_embedding(
        image_path
    )

    if embedding is None:

        if os.path.exists(
            image_path
        ):
            os.remove(
                image_path
            )

        raise HTTPException(
            400,
            "Face not detected"
        )

    current_user.face_embedding = embedding
    current_user.face_enabled = True

    db.commit()

    return {
        "message":
        "Face ID enabled successfully"
    }


@router.delete("/disable-face-id")
def disable_face_id(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    current_user.face_embedding = None
    current_user.face_enabled = False

    if current_user.role == "admin":
        path = f"app/media/faces/admin/{current_user.id}.jpg"

    else:
        path = f"app/media/faces/teacher/{current_user.id}.jpg"

    if os.path.exists(path):
        os.remove(path)

    db.commit()

    return {
        "message": "Face ID disabled"
    }



@router.get("/me")
def get_me(user = Depends(get_current_user)):
    return user

