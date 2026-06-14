from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.schemas.time_slot import TimeSlotCreate
from app.services.time_slot_services import (
    create_time_slot,
    get_all_time_slots,
    get_time_slot,
    delete_time_slot,
)

router = APIRouter(
    prefix="/time-slots",
    tags=["Time Slots"],
    dependencies=[Depends(require_role("admin"))]  # 🔥 HAMMASI admin
)


@router.post("/")
def create_time(
    data: TimeSlotCreate,
    db: Session = Depends(get_db)
):
    return create_time_slot(db, data)


@router.get("/")
def get_all(
    db: Session = Depends(get_db)
):
    return get_all_time_slots(db)


@router.get("/{time_slot_id}")
def get_one(
    time_slot_id: int,
    db: Session = Depends(get_db)
):
    return get_time_slot(db, time_slot_id)


@router.delete("/{time_slot_id}")
def delete(
    time_slot_id: int,
    db: Session = Depends(get_db)
):
    return delete_time_slot(db, time_slot_id)