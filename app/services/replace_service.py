from fastapi import HTTPException
from datetime import date
from sqlalchemy.orm import Session

from app.models.group import Group
from app.models.user import User
from app.models.replace import LessonReplacement


def create_replacement(
    db: Session,
    group_id: int,
    lesson_date: date,
    replacement_teacher_id: int
):

    group = db.query(Group).filter(
        Group.id == group_id
    ).first()

    if not group:
        raise HTTPException(404, "Group not found")

    replacement_teacher = db.query(User).filter(
        User.id == replacement_teacher_id,
        User.role == "teacher"
    ).first()

    if not replacement_teacher:
        raise HTTPException(404, "Replacement teacher not found")

    # 🔥 duplicate replacement check
    existing = db.query(LessonReplacement).filter(
        LessonReplacement.group_id == group_id,
        LessonReplacement.date == lesson_date
    ).first()

    if existing:
        raise HTTPException(
            400,
            "Replacement already exists for this group and date"
        )

    replacement = LessonReplacement(
        group_id=group.id,
        original_teacher_id=group.teacher_id,
        replacement_teacher_id=replacement_teacher_id,
        date=lesson_date
    )

    db.add(replacement)
    db.commit()
    db.refresh(replacement)

    return {
        "message": "Replacement created",

        "replacement": {
            "id": replacement.id,
            "date": str(replacement.date),

            "group": {
                "id": group.id,
                "name": group.name
            },

            "original_teacher": {
                "id": replacement.original_teacher.id,
                "full_name": replacement.original_teacher.full_name
            },

            "replacement_teacher": {
                "id": replacement.replacement_teacher.id,
                "full_name": replacement.replacement_teacher.full_name
            }
        }
    }