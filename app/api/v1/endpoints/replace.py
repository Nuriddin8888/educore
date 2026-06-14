from datetime import datetime
from sqlalchemy.orm import Session
from app.core.deps import get_db, require_role
from app.models.replace import LessonReplacement
from app.schemas.replace import ReplacementCreate
from fastapi import APIRouter, Depends, HTTPException
from app.services.replace_service import create_replacement


router = APIRouter(prefix="/replace", tags=["Replace Lesson"])

@router.get("/")
def replacement_list(
    month: str = None,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    query = db.query(LessonReplacement)

    # 🔥 month filter
    if month:

        start_date = datetime.strptime(
            month + "-01",
            "%Y-%m-%d"
        ).date()

        if start_date.month == 12:
            end_date = start_date.replace( year=start_date.year + 1,month=1)
        else:
            end_date = start_date.replace(
                month=start_date.month + 1
            )

        query = query.filter(
            LessonReplacement.date >= start_date,
            LessonReplacement.date < end_date
        )

    replacements = query.order_by(
        LessonReplacement.date.desc()
    ).all()

    result = []

    for r in replacements:

        result.append({
            "id": r.id,

            "date": str(r.date),

            "group": {
                "id": r.group.id,
                "name": r.group.name
            },

            "original_teacher": {
                "id": r.original_teacher.id,
                "full_name": r.original_teacher.full_name
            },

            "replacement_teacher": {
                "id": r.replacement_teacher.id,
                "full_name": r.replacement_teacher.full_name
            }
        })

    return result


@router.post("/")
def replace_teacher(
    data: ReplacementCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return create_replacement(
        db,
        data.group_id,
        data.date,
        data.replacement_teacher_id
    )



@router.get("/{replacement_id}")
def replacement_detail(
    replacement_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    replacement = db.query(LessonReplacement).filter(
        LessonReplacement.id == replacement_id
    ).first()

    if not replacement:
        raise HTTPException(404, "Replacement not found")

    return {
        "id": replacement.id,

        "date": str(replacement.date),

        "group": {
            "id": replacement.group.id,
            "name": replacement.group.name,
            "course": replacement.group.course_name
        },

        "original_teacher": {
            "id": replacement.original_teacher.id,
            "full_name": replacement.original_teacher.full_name
        },

        "replacement_teacher": {
            "id": replacement.replacement_teacher.id,
            "full_name": replacement.replacement_teacher.full_name
        },

        "students_count": len(replacement.group.students)
    }


