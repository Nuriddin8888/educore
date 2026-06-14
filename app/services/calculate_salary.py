from sqlalchemy import func
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from collections import defaultdict
from app.models.holiday import Holiday
from app.models.attendance import Attendance
from app.models.teacher_salary import TeacherSalary
from app.models.system_settings import SystemSettings
from app.core.constants import ATTENDANCE_ABSENT, ATTENDANCE_LABELS



def _calculate_salary_core(db, attendances):

    students_map = defaultdict(list)

    for att in attendances:
        students_map[att.student_id].append(att)

    total_salary = 0
    students_data = []

    for student_id, atts in students_map.items():

        consecutive_absent = 0
        days_paid = 0
        amount = 0

        attendance_days = []

        for att in atts:

            # 🔥 inactive student skip
            if not att.student or not att.student.is_active:
                continue

            # 🔥 unpaid holiday skip
            holiday = db.query(Holiday).filter(
                Holiday.date == att.date,
                Holiday.is_paid == False
            ).first()

            if holiday:
                continue

            # 🔥 teacher attendance qilmagan
            if not att.is_checked:
                continue

            # 🔥 absent counter
            if att.status == ATTENDANCE_ABSENT:
                consecutive_absent += 1
            else:
                consecutive_absent = 0

            # 🔥 4 ta ketma-ket absentdan keyin pul yo‘q
            counted = consecutive_absent < 4

            lesson_price = float(att.lesson_price or 0)

            attendance_days.append({
                "date": str(att.date),
                "time": str(att.lesson_start_time.time()) if att.lesson_start_time else None,
                "status": ATTENDANCE_LABELS.get(att.status),
                "lesson_price": lesson_price,
                "counted": counted
            })

            # 🔥 MAIN LOGIC
            if counted:
                amount += lesson_price
                days_paid += 1

        student = atts[0].student

        students_data.append({
            "student_id": student.id,
            "full_name": student.full_name,
            "days_paid": days_paid,
            "amount": round(amount, 2),
            "attendance_days": attendance_days
        })

        total_salary += amount

    return round(total_salary, 2), students_data


def calculate_teacher_salary(db, teacher_id: int, month: str):

    start_date = datetime.strptime(
        month + "-01",
        "%Y-%m-%d"
    ).date()

    if start_date.month == 12:
        end_date = start_date.replace(
            year=start_date.year + 1,
            month=1
        )
    else:
        end_date = start_date.replace(
            month=start_date.month + 1
        )

    teacher = db.query(User).filter(
        User.id == teacher_id
    ).first()

    if not teacher:
        raise HTTPException(404, "Teacher not found")

    if not teacher.grade_rel:
        raise HTTPException(400, "Teacher grade not set")

    attendances = db.query(Attendance).filter(
        Attendance.teacher_id == teacher_id,
        Attendance.date >= start_date,
        Attendance.date < end_date
    ).order_by(
        Attendance.student_id,
        Attendance.date
    ).all()

    # 🔥 CORE LOGIC
    total_salary, students = _calculate_salary_core(
        db,
        attendances
    )

    # 🔥 SETTINGS
    settings = db.query(SystemSettings).first()

    tax_percent = float(
        settings.tax_percent if settings else 0
    )

    tax_amount = total_salary * (tax_percent / 100)

    final_salary = total_salary - tax_amount

    return {
        "teacher_id": teacher.id,
        "teacher_name": teacher.full_name,
        "month": month,

        "total_salary": round(total_salary, 2),

        "tax_percent": tax_percent,

        "tax_amount": round(tax_amount, 2),

        "final_salary": round(final_salary, 2),

        "students": students
    }


def calculate_and_save_salary(
    db,
    teacher_id: int,
    month: str
):

    result = calculate_teacher_salary(
        db,
        teacher_id,
        month
    )

    existing = db.query(TeacherSalary).filter(
        TeacherSalary.teacher_id == teacher_id,
        TeacherSalary.month == month
    ).first()

    if existing:

        existing.total_salary = result["final_salary"]
        existing.created_at = datetime.utcnow()

        db.commit()
        db.refresh(existing)

        return existing

    salary = TeacherSalary(
        teacher_id=teacher_id,
        month=month,
        total_salary=result["final_salary"],
        created_at=datetime.utcnow()
    )

    db.add(salary)
    db.commit()
    db.refresh(salary)

    return salary


def calculate_teacher_salary_detailed(
    db,
    teacher_id: int,
    month: str
):

    return calculate_teacher_salary(
        db,
        teacher_id,
        month
    )


def get_today_salary(
    db: Session,
    teacher_id: int
):

    today = date.today()

    attendances = db.query(Attendance).filter(
        Attendance.teacher_id == teacher_id,
        Attendance.date <= today
    ).order_by(
        Attendance.student_id,
        Attendance.date
    ).all()

    students_map = defaultdict(list)

    for att in attendances:
        students_map[att.student_id].append(att)

    today_total = 0

    for student_id, atts in students_map.items():

        consecutive_absent = 0

        for att in atts:

            # inactive student
            if not att.student or not att.student.is_active:
                continue

            # unpaid holiday
            holiday = db.query(Holiday).filter(
                Holiday.date == att.date,
                Holiday.is_paid == False
            ).first()

            if holiday:
                continue

            # unchecked
            if not att.is_checked:
                continue

            # absent counter
            if att.status == ATTENDANCE_ABSENT:
                consecutive_absent += 1
            else:
                consecutive_absent = 0

            counted = consecutive_absent < 4

            if att.date == today and counted:
                today_total += float(att.lesson_price or 0)

    return round(today_total, 2)


