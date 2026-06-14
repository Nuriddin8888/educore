from datetime import datetime, date


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.group import Group
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.replace import LessonReplacement

from app.models.grade import TeacherGrade

from app.core.deps import get_db, require_role
from app.schemas.group import GroupDetailResponse
from app.schemas.teacher import ChangePassword, TeacherCreate, TeacherUpdate, TeacherCoinAction
from app.services.calculate_salary import calculate_teacher_salary, calculate_teacher_salary_detailed
from app.services.teacher_service import create_teacher, get_teacher_profile, get_teachers, give_monthly_teacher_bonus, teacher_give_coin

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post("/")
def create(
    data: TeacherCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))  # 🔥 faqat admin
):
    return create_teacher(db, data)


@router.get("/")
def list_teachers(
    search: str = None,       # 🔍 name + phone
    grade: str = None,        # 🎓 grade filter
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return get_teachers(db, search, grade, skip, limit)


@router.get("/me/dashboard")
def teacher_dashboard(
    month: str = None,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):

    if not month:
        month = datetime.now().strftime("%Y-%m")


    return get_teacher_profile(
        db,
        user.id,
        month
    )


@router.get("/me/salary")
def teacher_salary(
    month: str,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):

    return calculate_teacher_salary_detailed(
        db,
        user.id,
        month
    )


@router.put("/{teacher_id}/grade")
def update_teacher_grade(
    teacher_id: int,
    grade_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.role == "teacher"
    ).first()

    if not teacher:
        raise HTTPException(404, "Teacher not found")

    grade = db.query(TeacherGrade).filter_by(id=grade_id).first()
    if not grade:
        raise HTTPException(404, "Grade not found")

    teacher.grade_id = grade_id

    db.commit()
    db.refresh(teacher)

    return {
        "message": "Grade updated",
        "teacher": teacher.full_name,
        "new_grade": grade.name
    }



@router.put("/me/password")
def change_password(
    data: ChangePassword,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):
    # 🔥 1. eski parolni tekshiramiz
    if not verify_password(data.old_password, user.password):
        raise HTTPException(400, "Old password is incorrect")

    # 🔥 2. yangi parollar mosligini tekshiramiz
    if data.new_password != data.confirm_password:
        raise HTTPException(400, "Passwords do not match")

    # 🔥 3. eski bilan yangi bir xil bo'lmasin
    if verify_password(data.new_password, user.password):
        raise HTTPException(400, "New password cannot be same as old password")

    # 🔥 4. hash qilib saqlaymiz
    user.password = hash_password(data.new_password)

    db.commit()
    db.refresh(user)

    return {
        "message": "Password updated successfully"
    }


@router.get("/monthly")
def teacher_monthly_salary(
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):

    current_year = datetime.now().year

    months = [f"{current_year}-{str(m).zfill(2)}" for m in range(1, 13)]

    data = []

    for m in months:
        res = calculate_teacher_salary(db, user.id, m)
        data.append({
            "month": m,
            "salary": res["final_salary"]
        })

    return data


# @router.get("/groups")
# def my_groups(
#     db: Session = Depends(get_db),
#     user = Depends(require_role("teacher"))
# ):
#     groups = db.query(Group).filter(
#         Group.teacher_id == user.id,
#         Group.is_active == True
#     ).all()

#     result = []

#     for group in groups:
#         result.append({
#             "group_id": group.id,
#             "name": group.name,
#             "course": group.course_name,
#             "students_count": len(group.students)
#         })

#     return result


@router.get("/groups")
def my_groups(
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):

    today = date.today()

    # 🔥 own groups
    own_groups = db.query(Group).filter(
        Group.teacher_id == user.id,
        Group.is_active == True
    ).all()

    # 🔥 replacement groups
    replacements = db.query(LessonReplacement).filter(
        LessonReplacement.replacement_teacher_id == user.id,
        LessonReplacement.date == today
    ).all()

    replacement_group_ids = [
        r.group_id for r in replacements
    ]

    replacement_groups = db.query(Group).filter(
        Group.id.in_(replacement_group_ids),
        Group.is_active == True
    ).all()

    # 🔥 merge
    all_groups = {}

    for group in own_groups:
        all_groups[group.id] = {
            "group_id": group.id,
            "name": group.name,
            "course": group.course_name,
            "students_count": len(group.students),
            "is_replacement": False
        }

    for group in replacement_groups:

        # duplicate bo‘lmasin
        if group.id not in all_groups:

            all_groups[group.id] = {
                "group_id": group.id,
                "name": group.name,
                "course": group.course_name,
                "students_count": len(group.students),
                "is_replacement": True
            }

    return list(all_groups.values())


@router.get("/groups/{group_id}")
def group_detail(
    group_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):

    group = db.query(Group).filter(
        Group.id == group_id
    ).first()

    if not group:
        raise HTTPException(404, "Group not found")

    # 🔥 own groupmi
    allowed = group.teacher_id == user.id

    # 🔥 replacementmi
    if not allowed:

        replacement = db.query(LessonReplacement).filter(
            LessonReplacement.group_id == group.id,
            LessonReplacement.replacement_teacher_id == user.id,
            LessonReplacement.date == date.today()
        ).first()

        allowed = replacement is not None

    if not allowed:
        raise HTTPException(403, "Access denied")

    return {
        "group_id": group.id,
        "name": group.name,
        "course": group.course_name,
        "students_count": len(group.students),

        "room": group.room,

        "is_replacement": group.teacher_id != user.id,

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


# @router.get("/groups/{group_id}", response_model=GroupDetailResponse)
# def group_detail(
#     group_id: int,
#     db: Session = Depends(get_db),
#     user = Depends(require_role("teacher"))
# ):
#     group = db.query(Group).filter(
#         Group.id == group_id,
#         Group.teacher_id == user.id
#     ).first()

#     if not group:
#         raise HTTPException(404, "Group not found")

#     return {
#         "group_id": group.id,
#         "name": group.name,
#         "course": group.course_name,
#         "students_count": len(group.students),

#         "room": group.room,

#         "time": {
#             "id": group.time_slot.id,
#             "start": str(group.time_slot.start_time),
#             "end": str(group.time_slot.end_time)
#         } if group.time_slot else None,

#         "schedule": group.schedule or [],

#         "students": [
#             {
#                 "id": s.id,
#                 "full_name": s.full_name,
#                 "phone": s.phone_number,
#                 "is_active": s.is_active
#             }
#             for s in group.students
#         ]
#     }



@router.get("/students/{student_id}/attendance")
def student_attendance(
    student_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):
    student = db.query(Student).join(Student.group).filter(
        Student.id == student_id,
        Group.teacher_id == user.id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    records = db.query(Attendance).filter(
        Attendance.student_id == student_id
    ).order_by(Attendance.date.desc()).all()

    return {
        "student_id": student.id,
        "full_name": student.full_name,
        "attendance": [
            {
                "date": r.date,
                "status": r.status
            }
            for r in records
        ]
    }


@router.put("/{teacher_id}")
def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.role == "teacher"
    ).first()

    if not teacher:
        raise HTTPException(404, "Teacher not found")

    update_data = data.dict(exclude_unset=True)

    # 🔥 phone unique check
    if "phone_number" in update_data:
        existing = db.query(User).filter(
            User.phone_number == update_data["phone_number"],
            User.id != teacher_id
        ).first()

        if existing:
            raise HTTPException(400, "Phone already exists")

    # 🔥 update
    for key, value in update_data.items():
        if key == "password":
            value = hash_password(value)
        setattr(teacher, key, value)

    db.commit()
    db.refresh(teacher)

    return {
        "message": "Teacher updated",
        "data": teacher
    }



@router.post("/coin/manual")
def give_coin(
    data: TeacherCoinAction,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher"))
):

    return teacher_give_coin(db=db,teacher_id=user.id,data=data)


@router.post("/bonus/monthly")
def monthly_bonus(
    month: str,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return give_monthly_teacher_bonus(db, month)


@router.post("/admin/coin/manual")
def admin_give_coin(
    data: TeacherCoinAction,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    return teacher_give_coin(
        db=db,
        teacher_id=user.id,
        data=data,
        is_admin=True
    )


