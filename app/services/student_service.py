import os
import uuid
import string
import random
from sqlalchemy import func
from fastapi import HTTPException
from app.models.group import Group
from app.models.student import Student
from datetime import datetime, timedelta, date
from app.core.security import hash_password
from app.schemas.student import StudentLogin
from app.models.attendance import Attendance
from sqlalchemy.orm import Session, joinedload
from app.utils.qrcode import generate_qr_base64
from app.models.coin_transaction import CoinTransaction
from app.models.student_group_history import StudentGroupHistory
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.constants import ATTENDANCE_PRESENT, ATTENDANCE_ABSENT, ATTENDANCE_LABELS




def student_login(db: Session, data: StudentLogin):
    student = db.query(Student).filter(
        Student.student_code == data.student_code
    ).first()

    # Bir xil xabar
    if not student:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    if not verify_password(data.password, student.password):
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    # Faollikni tekshirish
    if not student.is_active:
        raise HTTPException(
            status_code=403,
            detail="Student is inactive"
        )

    access_token = create_access_token(
        {
            "sub": str(student.id),
            "role": "student",
            "user_type": "student"
        }
    )

    refresh_token = create_refresh_token(
        {
            "sub": str(student.id),
            "role": "student",
            "user_type": "student"
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

def generate_student_code(db):
    while True:
        code = str(random.randint(100000, 999999))
        exists = db.query(Student).filter(Student.student_code == code).first()
        if not exists:
            return code


def generate_password():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


def reset_student_password(
    db: Session,
    student_id: int
):

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    # 🔥 yangi password
    new_password = generate_password()

    # 🔥 hash
    student.password = hash_password(
        new_password
    )

    # 🔥 vaqtinchalik
    student.plain_password = new_password

    db.commit()
    db.refresh(student)

    # 🔥 yangi QR
    qr_base64 = generate_qr_base64(
        full_name=student.full_name,
        student_id=student.student_code,
        password=new_password,
        code=student.student_code
    )

    return {
        "student_code": student.student_code,
        "new_password": new_password,
        "qr": qr_base64
    }


def create_student(db, data):

    code = generate_student_code(db)
    raw_password = generate_password()

    student = Student(
        full_name=data.full_name,
        phone_number=data.phone_number,
        gender=data.gender,
        birth_date=data.birth_date,
        parent_phone=data.parent_phone,
        address=data.address,
        group_id=data.group_id,

        student_code=code,

        password=hash_password(raw_password),
        plain_password=raw_password
    )

    db.add(student)
    db.flush()

    if data.group_id:
        history = StudentGroupHistory(
            student_id=student.id,
            group_id=data.group_id,
            start_date=date.today()
        )
        
        db.add(history)

    db.commit()
    db.refresh(student)

    qr_base64 = generate_qr_base64(
        full_name=student.full_name,
        student_id=code,
        password=raw_password,
        code=code
    )

    return {
        "student_id": student.id,
        "student_code": code,
        "password": raw_password,
        "qr": qr_base64
    }


def get_student_balance(db: Session, student_id: int):

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    # 🔥 PAID
    total_paid = sum(
        p.amount for p in student.payments
    ) if student.payments else 0

    # 🔥 MONTHLY PRICE
    monthly_price = student.group.price if student.group else 0

    # 🔥 ACCOUNTING
    if total_paid >= monthly_price:
        advance_payment = total_paid - monthly_price
        debt = 0
    else:
        debt = monthly_price - total_paid
        advance_payment = 0

    return {
        "student_id": student.id,
        "group": student.group.name if student.group else None,

        "monthly_price": monthly_price,

        "paid": total_paid,

        "debt": debt,

        "advance_payment": advance_payment
    }


def get_student_profile(db: Session, student_id: int):
    student = db.query(Student).options(
    joinedload(Student.group).joinedload(Group.teacher),
    joinedload(Student.payments)
    ).filter(Student.id == student_id).first()

    if not student:
        return {"error": "Student topilmadi"}

    # 📊 Attendance hisoblash
    attendances = db.query(Attendance).filter(
        Attendance.student_id == student_id
    ).all()

    total = len(attendances)
    present = len([a for a in attendances if a.status == ATTENDANCE_PRESENT])
    absent = len([a for a in attendances if a.status == ATTENDANCE_ABSENT])

    percentage = int((present / total) * 100) if total > 0 else 0

    # 💰 Payment hisoblash
    total_paid = sum(p.amount for p in student.payments)

    group_price = student.group.price if student.group else 0
    debt = group_price - total_paid

    return {
        "id": student.id,
        "full_name": student.full_name,
        "group": student.group.name if student.group else None,
        "teacher": student.group.teacher.full_name if student.group and student.group.teacher else None,

        "attendance": {
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": percentage
        },

        "payments": {
            "total_paid": total_paid,
            "debt": debt
        }
    }


def get_student_attendance(db: Session, student_id: int):

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    attendances = db.query(Attendance).filter(
        Attendance.student_id == student_id
    ).order_by(Attendance.date.desc()).all()

    total_lessons = len(attendances)

    present_count = len([
        a for a in attendances if a.status == ATTENDANCE_PRESENT
    ])

    absent_count = len([
        a for a in attendances if a.status == ATTENDANCE_ABSENT
    ])

    late_count = len([
        a for a in attendances if a.status == "late"
    ])

    attendance_percent = 0

    if total_lessons > 0:
        attendance_percent = round(
            (present_count / total_lessons) * 100,
            1
        )

    return {
        "student_id": student.id,
        "student_name": student.full_name,

        "statistics": {
            "total_lessons": total_lessons,
            "present": present_count,
            "absent": absent_count,
            "late": late_count,
            "attendance_percent": attendance_percent
        },

        "attendances": [
            {
                "date": str(a.date),
                "status": ATTENDANCE_LABELS.get(a.status),
                "group_id": a.group_id,
                "group_name": a.group.name if a.group else None
            }
            for a in attendances
]
    }


def check_student_conflict(db, student_id: int, group_id: int):
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(404, "Student not found")

    new_group = db.query(Group).filter(Group.id == group_id).first()

    if not new_group:
        raise HTTPException(404, "Group not found")

    # student oldingi groupda bo‘lsa
    if student.group_id:
        current_group = db.query(Group).filter(Group.id == student.group_id).first()

        if current_group and current_group.time_slot_id == new_group.time_slot_id:
            raise HTTPException(
                status_code=400,
                detail="Student already has a class at this time"
            )
        

def update_student_service(db: Session, student_id: int, data):
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    update_data = data.dict(exclude_unset=True)

    # 🔥 phone unique check
    if "phone_number" in update_data:
        existing = db.query(Student).filter(
            Student.phone_number == update_data["phone_number"],
            Student.id != student_id
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Phone already exists")

    # 🔥 group mavjudligini tekshirish
    if "group_id" in update_data and update_data["group_id"] is not None:
        group = db.query(Group).filter(Group.id == update_data["group_id"]).first()

        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # 🔥 conflict check (eng muhim qism)
        if student.group_id and student.group_id != update_data["group_id"]:
            old_group = db.query(Group).filter(Group.id == student.group_id).first()

            if old_group and old_group.is_active:
                raise HTTPException(
                    status_code=400,
                    detail="Student already assigned to another active group"
                )

    # 🔥 update
    for key, value in update_data.items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)

    return student


def get_period_dates(period: str):

    today = datetime.utcnow()

    if period == "today":
        return today.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

    elif period == "week":
        return today - timedelta(days=7)

    elif period == "month":
        return today.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

    elif period == "year":
        return today.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

    # 🔥 YYYY-MM support
    try:
        return datetime.strptime(period, "%Y-%m")
    except ValueError:
        raise ValueError(
            "Invalid period"
        )



def get_global_leaderboard(db, period: str):

    start_date = get_period_dates(period)

    results = db.query(
        Student.id,
        Student.full_name,
        func.coalesce(func.sum(CoinTransaction.amount), 0).label("coins")
    ).join(
        CoinTransaction,
        CoinTransaction.student_id == Student.id
    ).filter(
        CoinTransaction.created_at >= start_date
    ).group_by(
        Student.id
    ).order_by(
        func.sum(CoinTransaction.amount).desc()
    ).limit(20).all()

    return [
        {
            "student_id": r.id,
            "full_name": r.full_name,
            "coins": int(r.coins)
        }
        for r in results
    ]



def get_group_leaderboard(db, student, period: str):

    if not student.group_id:
        return []

    start_date = get_period_dates(period)

    results = db.query(
        Student.id,
        Student.full_name,
        func.coalesce(func.sum(CoinTransaction.amount), 0).label("coins")
    ).join(
        CoinTransaction,
        CoinTransaction.student_id == Student.id
    ).filter(
        Student.group_id == student.group_id,
        CoinTransaction.created_at >= start_date
    ).group_by(
        Student.id
    ).order_by(
        func.sum(CoinTransaction.amount).desc()
    ).all()

    return [
        {
            "student_id": r.id,
            "full_name": r.full_name,
            "coins": int(r.coins)
        }
        for r in results
    ]


def upload_student_avatar(db, student, file):

    # 🔥 image check
    if file.content_type not in [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp"
    ]:
        raise HTTPException(400, "Invalid image")

    # 🔥 papka
    upload_dir = "app/media/avatars"

    os.makedirs(upload_dir, exist_ok=True)

    # 🔥 unique filename
    ext = file.filename.split(".")[-1]

    filename = f"{uuid.uuid4()}.{ext}"

    file_path = os.path.join(upload_dir, filename)

    # 🔥 save image
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    # 🔥 eski avatarni o‘chirish
    if student.avatar and student.avatar != "default.png":

        old_path = os.path.join(upload_dir, student.avatar)

        if os.path.exists(old_path):
            os.remove(old_path)

    # 🔥 db update
    student.avatar = filename

    db.commit()
    db.refresh(student)

    return {
        "message": "Avatar uploaded",
        "avatar": f"/media/avatars/{filename}"
    }



