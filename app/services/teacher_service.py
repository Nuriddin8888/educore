from sqlalchemy.orm import Session
from app.models.user import User
from app.models.group import Group
from app.models.teacher_coin import TeacherCoin
from sqlalchemy import or_

from app.core.security import hash_password
from app.models.attendance import Attendance
from app.models.grade import TeacherGrade
from datetime import datetime
from fastapi import HTTPException
from collections import defaultdict

from app.services.calculate_salary import get_today_salary, calculate_teacher_salary

from app.models.student import Student
from app.models.student_coin import StudentCoin
from app.models.coin_transaction import CoinTransaction, CoinTypeEnum
from app.models.holiday import Holiday
from app.schemas.teacher import TeacherCoinAction

from app.core.constants import ATTENDANCE_ABSENT, ATTENDANCE_LABELS



def create_teacher(db, data):
    default_grade = db.query(TeacherGrade).filter_by(name="junior").first()

    teacher = User(
        full_name=data.full_name,
        phone_number=data.phone_number,
        password=hash_password(data.password),
        role="teacher",
        grade_id=default_grade.id  # 🔥
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


def get_teachers(db: Session, search=None, grade=None, skip=0, limit=10):
    query = db.query(User).filter(User.role == "teacher")

    # 🔍 name + phone search
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.phone_number.ilike(f"%{search}%")
            )
        )

    # 🎓 grade filter
    if grade:
        query = query.join(User.grade_rel).filter(
            User.grade_rel.has(name=grade)
        )

    total = query.count()

    teachers = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "data": teachers
    }



def get_teacher_profile(
    db: Session,
    teacher_id: int,
    month: str
):

    teacher = db.query(User).filter(
        User.id == teacher_id
    ).first()

    if not teacher:
        raise HTTPException(404, "Teacher not found")

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

    # 🔥 BUGUNGI OYLIK
    today_salary = get_today_salary(
        db,
        teacher.id
    )

    # 🔥 OYLIK HISOBI
    salary_data = calculate_teacher_salary(
        db,
        teacher.id,
        month
    )

    attendances = db.query(Attendance).filter(
        Attendance.teacher_id == teacher_id,
        Attendance.date >= start_date,
        Attendance.date < end_date
    ).order_by(
        Attendance.group_id,
        Attendance.student_id,
        Attendance.date
    ).all()

    groups_map = defaultdict(lambda: {
        "group_id": None,
        "name": None,
        "students": {},
        "group_total_income": 0
    })

    students_map = defaultdict(list)

    for att in attendances:
        students_map[att.student_id].append(att)

    for student_id, atts in students_map.items():

        consecutive_absent = 0
        days_paid = 0
        amount = 0

        attendance_days = []

        for att in atts:

            # 🔥 BAYRAM CHECK
            holiday = db.query(Holiday).filter(
                Holiday.date == att.date,
                Holiday.is_paid == False
            ).first()

            if holiday:
                continue

            # 🔥 USTOZ DAVOMAT BELGILAMAGAN
            if not att.is_checked:
                continue

            # 🔥 ARXIV STUDENT
            if not att.student.is_active:
                continue

            # 🔥 ABSENT LOGIKA
            if att.status == ATTENDANCE_ABSENT:
                consecutive_absent += 1
            else:
                consecutive_absent = 0

            counted = consecutive_absent < 4

            lesson_price = float(att.lesson_price or 0)

            attendance_days.append({
                "date": str(att.date),
                "time": (
                    str(att.lesson_start_time.time())
                    if att.lesson_start_time else None
                ),
                "status": ATTENDANCE_LABELS.get(att.status),
                "lesson_price": lesson_price,
                "counted": counted
            })

            # 🔥 1-2-3 absent ham hisoblanadi
            if counted:
                amount += lesson_price
                days_paid += 1

        # 🔥 attendance yo‘q student skip
        if not atts:
            continue

        student = atts[0].student
        group = atts[0].group

        g = groups_map[group.id]

        g["group_id"] = group.id
        g["name"] = group.name

        g["group_total_income"] += amount

        g["students"][student.id] = {
            "student_id": student.id,
            "full_name": student.full_name,
            "days_paid": days_paid,
            "month_paid": amount,
            "attendance_days": attendance_days
        }

    result_groups = []

    for g in groups_map.values():

        result_groups.append({
            "group_id": g["group_id"],
            "name": g["name"],
            "students_count": len(g["students"]),
            "group_total_income": round(
                g["group_total_income"],
                2
            ),
            "students": list(g["students"].values())
        })

    return {
        "teacher": {
            "id": teacher.id,
            "full_name": teacher.full_name,
            "grade": (
                teacher.grade_rel.name
                if teacher.grade_rel else None
            )
        },

        "groups": result_groups,

        # 🔥 BUGUNGI DAROMAD
        "today_salary": today_salary,

        # 🔥 SOLIQDAN OLDIN
        "total_salary": salary_data["total_salary"],

        # 🔥 SOLIQ %
        "tax_percent": salary_data["tax_percent"],

        # 🔥 USHLANGAN SOLIQ
        "tax_amount": salary_data["tax_amount"],

        # 🔥 QO‘LGA TEGADIGAN
        "final_salary": salary_data["final_salary"]
    }


def give_monthly_teacher_bonus(db: Session, month: str):

    teachers = db.query(User).filter(User.role == "teacher").all()
    results = []

    for teacher in teachers:

        # 🔥 duplicate check
        existing = db.query(CoinTransaction).filter(
            CoinTransaction.teacher_id == teacher.id,
            CoinTransaction.type == "monthly_bonus",
            CoinTransaction.comment == f"{month} bonus"
        ).first()

        if existing:
            continue

        # 🔥 student count
        students_count = (db.query(Student.id)
        .join(Group, Student.group_id == Group.id)
        .filter(Group.teacher_id == teacher.id,Student.is_active == True)
        .distinct()
        .count()
        )

        bonus = students_count * 100

        if bonus == 0:
            continue

        # 🔥 coin
        coin = db.query(TeacherCoin).filter(
            TeacherCoin.teacher_id == teacher.id
        ).first()

        if not coin:
            coin = TeacherCoin(teacher_id=teacher.id, balance=0)
            db.add(coin)
            db.flush()

        coin.balance += bonus

        # 🔥 transaction
        tx = CoinTransaction(
            student_id=None,
            teacher_id=teacher.id,
            amount=bonus,
            type="monthly_bonus",
            comment=f"{month} bonus"
        )

        db.add(tx)

        results.append({
            "teacher_id": teacher.id,
            "students": students_count,
            "bonus": bonus,
            "new_balance": coin.balance
        })

    db.commit()

    return results


def teacher_give_coin(db: Session, teacher_id: int, data: TeacherCoinAction,is_admin: bool = False):
    student = db.query(Student).filter(
        Student.id == data.student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    # 🔥 TEACHER FAQAT O'Z STUDENTIGA
    if not is_admin:

        if not student.group:
            raise HTTPException(
                status_code=400,
                detail="Student has no group"
            )

        if student.group.teacher_id != teacher_id:
            raise HTTPException(
                status_code=403,
                detail="You can only manage your own students"
            )

    # 🔥 coin olish yoki yaratish
    coin = db.query(StudentCoin).filter(
        StudentCoin.student_id == student.id
    ).first()

    if not coin:
        coin = StudentCoin(
            student_id=student.id,
            balance=0
        )

        db.add(coin)
        db.flush()

    # 🔥 action
    if data.action == "add":
        coin.balance += data.amount
        tx_type = CoinTypeEnum.manual_add
        amount = data.amount

    else:

        if coin.balance < data.amount:
            raise HTTPException(
                status_code=400,
                detail="Not enough coin balance"
            )

        coin.balance -= data.amount

        tx_type = CoinTypeEnum.manual_subtract
        amount = -data.amount

    # 🔥 transaction
    tx = CoinTransaction(
        student_id=student.id,
        teacher_id=teacher_id,
        amount=amount,
        type=tx_type,
        comment=data.comment
    )

    db.add(tx)

    db.commit()

    return {
        "message": "coin updated",
        "student_id": student.id,
        "new_balance": coin.balance
    }


