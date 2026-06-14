from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.schemas.attendance import AttendanceCreate
from app.services.attendance_service import mark_attendance, get_student_stats, get_student_full_attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/mark")
def mark(
    data: AttendanceCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):
    return mark_attendance(db, data, user)


@router.get("/student/{student_id}")
def student_stats(
    student_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):
    return get_student_stats(db, student_id)


@router.get("/student/{student_id}/history")
def student_history(
    student_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):
    return get_student_full_attendance(db, student_id)