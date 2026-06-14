import random

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.group import Group
from app.models.group_teacher_history import GroupTeacherHistory
from app.models.user import User
from app.models.room import Room
from app.models.time_slot import TimeSlot
from app.models.attendance import Attendance
from app.core.constants import ATTENDANCE_LABELS

from datetime import date

def format_datetime(dt):
    if not dt:
        return None

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_group(db, data):
    validate_teacher(db, data.teacher_id)
    validate_room(db, data.room_id)
    validate_time_slot(db, data.time_slot_id)

    # 🔥 conflict check
    check_group_conflict(db, data.room_id, data.time_slot_id, data.schedule)

    # 🔥 teacher conflict
    check_teacher_conflict(db, data.teacher_id, data.time_slot_id, data.schedule)

    group_name = generate_group_name(db, data.course_name)

    group = Group(
        name=group_name,
        course_name=data.course_name,
        teacher_id=data.teacher_id,
        price=data.price,
        start_date=data.start_date,
        schedule=data.schedule,
        room_id=data.room_id,
        time_slot_id=data.time_slot_id
    )

    db.add(group)
    db.flush()

    history = GroupTeacherHistory(
        group_id=group.id,
        teacher_id=data.teacher_id,
        start_date=data.start_date
    )

    db.add(history)

    db.commit()
    db.refresh(group)

    return group


def get_groups(
    db: Session,
    search: str = None,
    teacher_name: str = None,
    course_name: str = None,
    is_active: bool = None,
    skip: int = 0,
    limit: int = 10
):
    query = db.query(Group).join(User, Group.teacher_id == User.id)

    # 🔍 group name search
    if search:
        query = query.filter(Group.name.ilike(f"%{search}%"))

    # 🔥 teacher name bo‘yicha
    if teacher_name:
        query = query.filter(User.full_name.ilike(f"%{teacher_name}%"))

    # 🔥 course bo‘yicha
    if course_name:
        query = query.filter(Group.course_name.ilike(f"%{course_name}%"))

    # 🔥 active filter (agar mavjud bo‘lsa)
    if is_active is not None:
        query = query.filter(Group.is_active == is_active)

    total = query.count()

    groups = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "data": [
            {
                "id": g.id,
                "name": g.name,
                "course_name": g.course_name,
                "teacher": {
                    "id": g.teacher.id,
                    "full_name": g.teacher.full_name
                } if g.teacher else None,
                "price": g.price,
                "start_date": g.start_date,
                "is_active": g.is_active
            }
            for g in groups
        ]
    }


def get_group_detail(db: Session, group_id: int):
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        return None

    return {
        "group_id": group.id,
        "name": group.name,
        "course": group.course_name,
        "students_count": len(group.students),

        "room": group.room,

        "time": {
            "id": group.time_slot.id,
            "start": str(group.time_slot.start_time),
            "end": str(group.time_slot.end_time)
        } if group.time_slot else None,

        "schedule": group.schedule or [],

        "students": [
            {
                "id": s.id,
                "full_name": s.full_name,
                "phone": s.phone_number,
                "is_active": s.is_active
            }
            for s in group.students
        ]
    }



def get_group_attendance(db: Session, group_id: int):

    records = db.query(Attendance).filter(
        Attendance.group_id == group_id
    ).all()

    result = []

    for att in records:
        result.append({
            "id": att.id,
            "student_id": att.student_id,
            "group_id": att.group_id,
            "teacher_id": att.teacher_id,
            "status": ATTENDANCE_LABELS.get(att.status),
            "teacher_grade_name": att.teacher_grade_name,
            "date": str(att.date),
            "lesson_price": att.lesson_price,

            # 🔥 formatlangan vaqtlar
            "lesson_start_time": format_datetime(att.lesson_start_time),
            "created_at": format_datetime(att.created_at)
        })

    return result


def generate_group_name(db, course_name: str):
    prefix_map = {
        "backend": "nB",
        "frontend": "nF",
        "beginner": "nBG",
        "kids": "IK"
    }

    prefix = prefix_map.get(course_name.lower(), "nX")

    while True:
        number = random.randint(100, 9999)
        name = f"{prefix}-{number}"

        exists = db.query(Group).filter(Group.name == name).first()
        if not exists:
            return name
        


def validate_teacher(db, teacher_id: int):
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher



def update_group_service(db, group_id: int, data):
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(404, "Group not found")

    # yangi qiymatlarni aniqlaymiz
    new_room_id = data.room_id if data.room_id is not None else group.room_id
    new_time_slot_id = data.time_slot_id if data.time_slot_id is not None else group.time_slot_id

    # 🔥 conflict check
    check_group_conflict(db, new_room_id, new_time_slot_id, group_id)
    new_teacher_id = data.teacher_id if data.teacher_id is not None else group.teacher_id

    check_teacher_conflict(db, new_teacher_id, new_time_slot_id, group_id)

    if data.teacher_id is not None:
        validate_teacher(db, data.teacher_id)

    if data.room_id is not None:
        validate_room(db, data.room_id)

    if data.time_slot_id is not None:
        validate_time_slot(db, data.time_slot_id)

    for key, value in data.dict(exclude_unset=True).items():
        setattr(group, key, value)

    db.commit()
    db.refresh(group)

    return group



def change_group_status_service(db, group_id: int, is_active: bool):
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group.is_active = is_active

    db.commit()

    return group



def validate_room(db, room_id):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")


def validate_time_slot(db, time_slot_id):
    slot = db.query(TimeSlot).filter(TimeSlot.id == time_slot_id).first()
    if not slot:
        raise HTTPException(404, "Time slot not found")
    

def check_group_conflict(db, room_id, time_slot_id, schedule):
    groups = db.query(Group).filter(
        Group.room_id == room_id,
        Group.time_slot_id == time_slot_id,
        Group.is_active == True
    ).all()

    for group in groups:
        # 🔥 schedule overlap check
        if set(group.schedule) & set(schedule):
            raise HTTPException(
                status_code=400,
                detail="This room is already occupied at this time for selected days"
            )
    

def check_teacher_conflict(db, teacher_id, time_slot_id, schedule):
    groups = db.query(Group).filter(
        Group.teacher_id == teacher_id,
        Group.time_slot_id == time_slot_id,
        Group.is_active == True
    ).all()

    for group in groups:
        if set(group.schedule) & set(schedule):
            raise HTTPException(
                status_code=400,
                detail="Teacher already has a group at this time"
            )
        


def change_group_teacher(db, group_id: int, new_teacher_id: int):
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(404, "Group not found")

    new_teacher = db.query(User).filter(User.id == new_teacher_id).first()

    if not new_teacher:
        raise HTTPException(404, "New teacher not found")

    today = date.today()

    # 🔥 eski history yopamiz
    current_history = db.query(GroupTeacherHistory).filter(
        GroupTeacherHistory.group_id == group_id,
        GroupTeacherHistory.end_date == None
    ).first()

    if current_history:
        current_history.end_date = today

    # 🔥 yangi history ochamiz
    new_history = GroupTeacherHistory(
        group_id=group_id,
        teacher_id=new_teacher_id,
        start_date=today
    )

    db.add(new_history)

    # 🔥 groupni ham update qilamiz (current uchun)
    group.teacher_id = new_teacher_id

    db.commit()

    return {
        "message": "Teacher changed successfully",
        "group_id": group_id,
        "new_teacher_id": new_teacher_id
    }


