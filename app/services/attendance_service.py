from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.group import Group
from app.models.holiday import Holiday
from app.models.student import Student
from datetime import timedelta, datetime
from app.models.attendance import Attendance
from app.models.student_coin import StudentCoin
from app.models.replace import LessonReplacement
from app.models.coin_transaction import CoinTransaction
from app.utils.attendance_utils import validate_attendance_time
from app.models.student_group_history import StudentGroupHistory
from app.core.constants import ATTENDANCE_PRESENT, ATTENDANCE_LABELS



def get_student_stats(db: Session, student_id: int):
    records = db.query(Attendance).filter(
        Attendance.student_id == student_id
    ).all()

    total = len(records)
    present = sum(1 for r in records if r.status == ATTENDANCE_PRESENT)
    absent = total - present

    percent = (present / total * 100) if total > 0 else 0

    return {
        "student_id": student_id,
        "total": total,
        "present": present,
        "absent": absent,
        "percentage": round(percent, 2)
    }


def get_group_attendance(db: Session, group_id: int):
    return db.query(Attendance).filter(Attendance.group_id == group_id).all()


def get_student_full_attendance(db: Session, student_id: int):
    records = db.query(Attendance).filter(
        Attendance.student_id == student_id
    ).all()

    total = len(records)
    present = sum(1 for r in records if r.status == ATTENDANCE_PRESENT)
    absent = total - present

    history = [
        {
            "date": r.date,
            "status": ATTENDANCE_LABELS.get(r.status)
        }
        for r in records
    ]

    return {
        "student_id": student_id,
        "total": total,
        "present": present,
        "absent": absent,
        "percentage": round((present / total * 100), 2) if total else 0,
        "history": history
    }


def mark_attendance(db: Session, data, current_user):

    group = db.query(Group).filter(Group.id == data.group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")
    
    # 🔥 TIME SLOT CHECK
    if not group.time_slot or not group.time_slot.start_time:
        raise HTTPException(400, "Group time is not set")

    # 🔥 replace tekshiramiz
    replacement = db.query(LessonReplacement).filter(
        LessonReplacement.group_id == group.id,
        LessonReplacement.date == data.date
    ).first()

    # 🔥 kim dars o'tyapti
    teacher_id = replacement.replacement_teacher_id if replacement else group.teacher_id

    # 🔥 permission
    if current_user.id != teacher_id:
        raise HTTPException(403, "You are not allowed to mark attendance for this lesson")

    # 🔥 vaqt check
    today = validate_attendance_time(group)
    if data.date != today:
        raise HTTPException(400, "You can only mark attendance for today")

    # 🔥 student
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(404, "Student not found")

    if not student.is_active:
        raise HTTPException(400, "Student is inactive")
    
    holiday = db.query(Holiday).filter(
        Holiday.date == data.date
    ).first()

    if holiday:
        raise HTTPException(
            400,
            f"{holiday.name} holiday. Attendance disabled"
        )


    # 🔥 HISTORY CHECK
    history = db.query(StudentGroupHistory).filter(
        StudentGroupHistory.student_id == student.id,
        StudentGroupHistory.start_date <= data.date,
        (StudentGroupHistory.end_date == None) |
        (StudentGroupHistory.end_date >= data.date)
    ).first()

    if not history:
        raise HTTPException(400, "Student not assigned to any group at this date")

    if history.group_id != group.id:
        raise HTTPException(400, "Student not in this group on this date")

    # 🔥 UPDATE OR CREATE
    existing = db.query(Attendance).filter(
        Attendance.student_id == student.id,
        Attendance.group_id == group.id,
        Attendance.date == data.date
    ).first()

    if existing:
        old_status = existing.status

        existing.status = data.status
        existing.group_id = group.id
        existing.teacher_id = teacher_id
        existing.is_checked = True

        db.commit()
        db.refresh(existing)

        # 🔥 faqat absent → present bo‘lsa coin beramiz
        if old_status != ATTENDANCE_PRESENT and data.status == ATTENDANCE_PRESENT:
            handle_attendance_coin(db, existing, group)
            db.commit()

        return {
            "message": "updated",

            "attendance": {
                "id": existing.id,
                "student_id": existing.student_id,
                "student_name": student.full_name,
                "group_id": existing.group_id,
                "date": str(existing.date),
                "status": existing.status,
                "lesson_price": existing.lesson_price
            }
        }
    
    lesson_teacher = db.query(User).filter(
    User.id == teacher_id
    ).first()

    lesson_price = 0
    grade_name = None

    if lesson_teacher and lesson_teacher.grade_rel:
        lesson_price = lesson_teacher.grade_rel.price_per_lesson
        grade_name = lesson_teacher.grade_rel.name

    attendance = Attendance(
        student_id=student.id,
        group_id=group.id,
        teacher_id=teacher_id,
        date=data.date,
        status=data.status,
        is_checked=True,

        lesson_start_time=datetime.combine(
            data.date,
            group.time_slot.start_time
        ),

        lesson_price=lesson_price,

        teacher_grade_name=grade_name
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    # 🔥 COIN BERAMIZ
    handle_attendance_coin(db, attendance, group)
    db.commit()

    return {
    "message": "created",

    "attendance": {
        "id": attendance.id,
        "student_id": attendance.student_id,
        "student_name": student.full_name,
        "group_id": attendance.group_id,
        "date": str(attendance.date),
        "status": ATTENDANCE_LABELS.get(attendance.status),
        "lesson_price": attendance.lesson_price
    }
}


def add_coin(db, student_id: int, amount: int, type: str, teacher_id=None):
    coin = db.query(StudentCoin).filter_by(student_id=student_id).first()

    if not coin:
        coin = StudentCoin(student_id=student_id, balance=0)
        db.add(coin)
        db.flush()

    coin.balance += amount

    transaction = CoinTransaction(
        student_id=student_id,
        teacher_id=teacher_id,
        amount=amount,
        type=type
    )

    db.add(transaction)


def handle_attendance_coin(db, attendance, group):
    # 🔥 faqat present bo‘lsa
    if attendance.status != ATTENDANCE_PRESENT:
        return

    lesson_time = attendance.lesson_start_time
    mark_time = attendance.created_at

    if not lesson_time:
        return

    diff = mark_time - lesson_time

    if diff <= timedelta(minutes=5):
        coin = 2
    else:
        coin = 1

    add_coin(
        db,
        student_id=attendance.student_id,
        amount=coin,
        type="attendance",
        teacher_id=attendance.teacher_id
    )


