from sqlalchemy import func
from datetime import datetime
from calendar import monthrange
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.group import Group
from collections import defaultdict
from datetime import date, timedelta
from app.models.student import Student
from app.models.payment import Payment
from app.models.holiday import Holiday
from app.models.attendance import Attendance
from app.models.system_settings import SystemSettings
from app.core.constants import ATTENDANCE_PRESENT, ATTENDANCE_ABSENT, ATTENDANCE_LABELS


ACTIVE_STATUSES = ["active", "frozen"]

EVEN_DAYS = [0, 2, 4]
ODD_DAYS = [1, 3, 5]



def get_dashboard(db: Session):

    total_students = db.query(Student).count()

    active_students = db.query(Student).filter(
        Student.status == "active"
    ).count()

    frozen_students = db.query(Student).filter(
        Student.status == "frozen"
    ).count()

    graduated_students = db.query(Student).filter(
        Student.status == "graduated"
    ).count()

    archived_students = db.query(Student).filter(
        Student.status == "archived"
    ).count()

    total_groups = db.query(Group).count()

    total_teachers = db.query(User).filter(
        User.role == "teacher"
    ).count()

    # 💰 total income
    total_income = db.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).scalar()

    system_settings = db.query(SystemSettings).first()

    # ❗ qarzdorlar
    students = db.query(Student).all()

    debtors_count = 0

    for student in students:

        if not student.group:
            continue

        total_paid = sum(
            p.amount for p in student.payments
        )

        group_price = student.group.price or 0

        debt = group_price - total_paid

        if debt > 0:
            debtors_count += 1

    return {

        # 👨‍🎓 STUDENTS
        "total_students": total_students,
        "active_students": active_students,
        "frozen_students": frozen_students,
        "graduated_students": graduated_students,
        "archived_students": archived_students,

        # 👨‍🏫 SYSTEM
        "total_groups": total_groups,
        "total_teachers": total_teachers,

        # 💰 FINANCE
        "total_income": float(total_income),
        "debtors_count": debtors_count,
        "tax_percent": system_settings.tax_percent if system_settings else 0
    }



def get_advanced_dashboard(db: Session):

    # =========================================
    # 📊 MONTHLY INCOME
    # =========================================

    payments = db.query(Payment).all()

    monthly = defaultdict(float)

    for p in payments:

        if not p.month:
            continue

        try:

            # 🔥 string bo‘lsa
            if isinstance(p.month, str):

                try:
                    dt = datetime.strptime(
                        p.month,
                        "%Y-%m"
                    )

                except ValueError:

                    dt = datetime.strptime(
                        p.month,
                        "%Y-%m-%d"
                    )

            else:
                dt = p.month

            key = dt.strftime("%Y-%m")

            monthly[key] += float(p.amount)

        except Exception:
            continue

    monthly_income = [
        {
            "month": month,
            "income": income
        }
        for month, income in sorted(monthly.items())
    ]

    # =========================================
    # 🏫 TOP DEBTOR GROUP
    # =========================================

    groups = db.query(Group).all()

    group_debts = {}

    for group in groups:

        total_group_debt = 0

        for student in group.students:

            # 🔥 archived/graduated/transferred skip
            if student.status not in ACTIVE_STATUSES:
                continue

            total_paid = sum(
                float(payment.amount)
                for payment in student.payments
            )

            debt = float(group.price) - total_paid

            if debt > 0:
                total_group_debt += debt

        group_debts[group.name] = total_group_debt

    top_debtor_group = None

    if group_debts:
        top_debtor_group = max(
            group_debts,
            key=group_debts.get
        )

    # =========================================
    # 🧑‍🎓 TOP STUDENT
    # =========================================

    top_student_query = (
        db.query(
            Student.full_name,
            func.count(Attendance.id).label("present_count")
        )
        .join(
            Attendance,
            Attendance.student_id == Student.id
        )
        .filter(
            Attendance.status == ATTENDANCE_PRESENT,
            Student.status.in_(ACTIVE_STATUSES)
        )
        .group_by(Student.id)
        .order_by(
            func.count(Attendance.id).desc()
        )
        .first()
    )

    top_student = None

    if top_student_query:
        top_student = {
            "full_name": top_student_query.full_name,
            "present_count": top_student_query.present_count
        }

    # =========================================
    # 👨‍🎓 TOTAL STUDENTS
    # =========================================

    total_students = db.query(Student).filter(
        Student.status.in_(ACTIVE_STATUSES)
    ).count()

    # =========================================
    # 🏫 TOTAL GROUPS
    # =========================================

    total_groups = db.query(Group).filter(
        Group.is_active == True
    ).count()

    # =========================================
    # 💰 TOTAL INCOME
    # =========================================

    total_income = db.query(
        func.coalesce(
            func.sum(Payment.amount),
            0
        )
    ).scalar()

    return {

        "statistics": {

            "total_students": total_students,

            "total_groups": total_groups,

            "total_income": float(total_income)
        },

        "monthly_income": monthly_income,

        "top_debtor_group": {
            "group_name": top_debtor_group,
            "debt": group_debts.get(top_debtor_group, 0)
        } if top_debtor_group else None,

        "top_student": top_student
    }


def calculate_student_payment(
    db: Session,
    group_id: int,
    join_date: date
):

    group = db.query(Group).filter(
        Group.id == group_id
    ).first()

    if not group:
        raise HTTPException(404, "Group not found")

    if not group.schedule:
        raise HTTPException(
            400,
            "Group schedule not found"
        )

    # 🔥 schedule example:
    # ["monday", "wednesday", "friday"]

    lesson_days = [int(day) for day in group.schedule]

    year = join_date.year
    month = join_date.month

    last_day = monthrange(year, month)[1]

    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    # =========================================
    # 📚 OY BO'YICHA JAMI DARSLAR
    # =========================================

    total_lessons = 0

    current = month_start

    while current <= month_end:

        if current.weekday() in lesson_days:
            total_lessons += 1

        current += timedelta(days=1)

    # =========================================
    # 📚 QOLGAN DARSLAR
    # =========================================

    remaining_lessons = 0

    current = join_date

    while current <= month_end:

        if current.weekday() in lesson_days:
            remaining_lessons += 1

        current += timedelta(days=1)

    if total_lessons == 0:
        raise HTTPException(
            400,
            "No lessons in this month"
        )

    # =========================================
    # 💰 HISOB
    # =========================================

    lesson_price = float(group.price) / total_lessons

    total_payment = round(
        lesson_price * remaining_lessons,
        2
    )

    return {

        "group_id": group.id,
        "group_name": group.name,

        "monthly_price": float(group.price),

        "join_date": join_date,

        "total_lessons_in_month": total_lessons,

        "remaining_lessons": remaining_lessons,

        "lesson_price": round(lesson_price, 2),

        "must_pay": total_payment
    }


def get_groups_schedule_dashboard(
    db: Session,
    schedule_type: str | None = None
):

    # =========================================
    # 🔥 FILTER DAYS
    # =========================================

    if schedule_type == "even":
        target_days = EVEN_DAYS

    elif schedule_type == "odd":
        target_days = ODD_DAYS

    else:
        # default = today
        today_weekday = datetime.today().weekday()
        target_days = [today_weekday]

    # =========================================
    # 🔥 GROUPS
    # =========================================

    groups = db.query(Group).all()

    result = []

    for group in groups:

        if not group.schedule:
            continue

        group_days = [
            int(day)
            for day in group.schedule
        ]

        if any(day in target_days for day in group_days):

            result.append({
                "group_id": group.id,
                "group_name": group.name,
                "course_name": group.course_name,

                "teacher": (
                    group.teacher.full_name
                    if group.teacher else None
                ),

                "room": (
                    group.room.name
                    if group.room else None
                ),

                "time_slot": f"{group.time_slot.start_time.strftime('%H:%M')} - {group.time_slot.end_time.strftime('%H:%M')}",

                "students_count": len(group.students),

                "schedule": group.schedule
            })

    return {
        "filter": schedule_type or "today",
        "groups_count": len(result),
        "groups": result
    }


def remove_holiday(db: Session, holiday_id: int):

    holiday = db.query(Holiday).filter(
        Holiday.id == holiday_id
    ).first()

    if not holiday:
        raise HTTPException(404, "Holiday not found")

    db.delete(holiday)
    db.commit()

    return {
        "message": "Holiday deleted successfully"
    }


def get_group_calendar(db: Session, group_id: int,month: str):
    group = db.query(Group).filter(
        Group.id == group_id
    ).first()

    if not group:
        raise HTTPException(404, "Group not found")

    # 🔥 month parse
    year, month_num = map(int, month.split("-"))

    # 🔥 month days
    days_in_month = monthrange(year, month_num)[1]

    start_date = date(year, month_num, 1)
    end_date = date(year, month_num, days_in_month)

    # 🔥 holidays
    holidays = db.query(Holiday).filter(
        Holiday.date >= start_date,
        Holiday.date <= end_date
    ).all()

    holiday_map = {
        h.date: h for h in holidays
    }

    # 🔥 attendances
    attendances = db.query(Attendance).filter(
        Attendance.group_id == group.id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()

    attendance_dates = {
        att.date for att in attendances
    }

    today = date.today()

    calendar_data = []

    current_day = start_date

    while current_day <= end_date:

        weekday = current_day.weekday()

        # 🔥 lesson kuni emas
        if weekday not in group.schedule:
            current_day += timedelta(days=1)
            continue

        item = {
            "date": str(current_day),
            "weekday": weekday
        }

        # 🔥 holiday
        holiday = holiday_map.get(current_day)

        if holiday:
            item["type"] = "holiday"
            item["holiday_name"] = holiday.name
            item["is_paid"] = holiday.is_paid

        # 🔥 attendance olingan
        elif current_day in attendance_dates:
            item["type"] = "attendance_taken"

        # 🔥 kelajakdagi lesson
        elif current_day > today:
            item["type"] = "future_lesson"

        # 🔥 oddiy lesson
        else:
            item["type"] = "lesson"

        calendar_data.append(item)

        current_day += timedelta(days=1)

    return {
        "group_id": group.id,
        "group_name": group.name,
        "month": month,
        "calendar": calendar_data
    }

