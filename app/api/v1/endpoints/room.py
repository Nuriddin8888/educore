from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models.room import Room

router = APIRouter(prefix="/rooms", tags=["Room"])


@router.post("/")
def create_room(name: str, db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    room = Room(name=name)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/")
def get_rooms(db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    return db.query(Room).all()


@router.delete("/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    room = db.query(Room).filter(Room.id == room_id).first()

    if not room:
        raise HTTPException(404, "Room not found")

    db.delete(room)
    db.commit()

    return {"message": "Room deleted"}