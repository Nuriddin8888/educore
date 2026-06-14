from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.teacher_salary import TeacherSalary
from app.schemas.salary import TeacherSalaryOut
from app.core.deps import get_db, require_role
from app.services.calculate_salary import calculate_and_save_salary

router = APIRouter(prefix="/salary", tags=["Salary"])


@router.post("/calculate")
def calculate_salary(
    month: str,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    teachers = db.query(User).filter(
        User.role == "teacher"
    ).all()

    result = []

    for teacher in teachers:

        salary = calculate_and_save_salary(
            db,
            teacher.id,
            month
        )

        result.append({
            "teacher_id": teacher.id,
            "teacher_name": teacher.full_name,
            "salary": salary.total_salary
        })

    return {
        "month": month,
        "teachers": result
    }


@router.get("/month/{month}")
def get_month_salary(
    month: str,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    salaries = db.query(TeacherSalary).filter(
        TeacherSalary.month == month
    ).all()

    return [
        {
            "teacher_id": s.teacher_id,
            "teacher_name": s.teacher.full_name,
            "salary": s.total_salary,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for s in salaries
    ]


