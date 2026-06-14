from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.grade import TeacherGrade
from app.schemas.grade import GradeCreate, GradeUpdate


def get_all(db: Session, skip: int = 0, limit: int = 10):
    return db.query(TeacherGrade).offset(skip).limit(limit).all()


def create(db: Session, data: GradeCreate):
    existing = db.query(TeacherGrade).filter(
        TeacherGrade.name == data.name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Grade already exists")

    grade = TeacherGrade(
        name=data.name,
        price_per_lesson=data.price
    )

    try:
        db.add(grade)
        db.commit()
        db.refresh(grade)
    except:
        db.rollback()
        raise

    return grade


def update(db: Session, grade_id: int, data: GradeUpdate):
    grade = db.query(TeacherGrade).filter(
        TeacherGrade.id == grade_id
    ).first()

    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    # duplicate check
    if data.name:
        existing = db.query(TeacherGrade).filter(
            TeacherGrade.name == data.name,
            TeacherGrade.id != grade_id
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Grade already exists")

    if data.name is not None:
        grade.name = data.name

    if data.price is not None:
        grade.price_per_lesson = data.price

    try:
        db.commit()
        db.refresh(grade)
    except:
        db.rollback()
        raise

    return grade


def delete(db: Session, grade_id: int):
    grade = db.query(TeacherGrade).filter(
        TeacherGrade.id == grade_id
    ).first()

    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    try:
        db.delete(grade)
        db.commit()
    except:
        db.rollback()
        raise