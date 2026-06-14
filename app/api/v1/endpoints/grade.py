from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.schemas.grade import GradeCreate, GradeUpdate, GradeResponse
from app.services import grade_service

router = APIRouter(prefix="/grades", tags=["Grades"])


# ✅ GET (pagination bilan)
@router.get("/", response_model=list[GradeResponse])
def get_grades(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return grade_service.get_all(db, skip, limit)


# ✅ CREATE
@router.post("/", response_model=GradeResponse, status_code=201)
def create_grade(
    data: GradeCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
):
    return grade_service.create(db, data)


# ✅ UPDATE
@router.put("/{grade_id}", response_model=GradeResponse)
def update_grade(
    grade_id: int,
    data: GradeUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
):
    return grade_service.update(db, grade_id, data)


# ✅ DELETE
@router.delete("/{grade_id}", status_code=204)
def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
):
    grade_service.delete(db, grade_id)