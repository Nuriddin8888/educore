import pytz

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import Response

from fastapi import UploadFile, File
from datetime import date, datetime

from app.models.coin_transaction import CoinTransaction
from app.utils.qrcode import generate_card_pdf
from app.utils.levels import get_student_level
from sqlalchemy.orm import Session, joinedload


from app.core.deps import get_db, require_role, get_current_student
from app.models.student import Student
from app.models.student_notes import StudentNote
from app.models.group import Group
from app.models.student_history import StudentStatusHistory
from app.models.student_group_history import StudentGroupHistory

from app.schemas.student import StudentCreate, StudentUpdate, StudentLogin, StudentStatusUpdate, StudentNoteCreate, ChangeStudentPassword
from app.services.student_service import create_student, get_student_balance, update_student_service, student_login, get_global_leaderboard, get_group_leaderboard, upload_student_avatar, get_student_attendance, reset_student_password



router = APIRouter(prefix="/students", tags=["Students"])


UZ_TZ = pytz.timezone("Asia/Tashkent")


@router.post("/login")
def login(data: StudentLogin, db: Session = Depends(get_db)):
    return student_login(db, data)


@router.get("/me")
def student_profile(
    current_student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    student = db.query(Student).options(
        joinedload(Student.group)
            .joinedload(Group.teacher),
        joinedload(Student.group)
            .joinedload(Group.time_slot),
        joinedload(Student.group)
            .joinedload(Group.room),
        joinedload(Student.coin)
    ).filter(Student.id == current_student.id).first()

    if not student:
        raise HTTPException(404, "Student not found")

    group = student.group
    time_slot = group.time_slot if group else None
    room = group.room if group else None
    coins = student.coin.balance if student.coin else 0
    level = get_student_level(coins)

    return {
        "id": student.id,
        "full_name": student.full_name,
        "phone": student.phone_number,
        "avatar": f"/media/avatars/{student.avatar or 'default.png'}",

        # 🔥 GROUP INFO
        "group": {
            "id": group.id if group else None,
            "name": group.name if group else None,
            "course": group.course_name if group else None,
        } if group else None,

        # 🔥 TEACHER
        "teacher": {
            "id": group.teacher.id,
            "full_name": group.teacher.full_name
        } if group and group.teacher else None,

        # 🔥 ROOM
        "room": {
            "id": room.id,
            "name": room.name
        } if room else None,

        # 🔥 TIME
        "time": {
            "start": str(time_slot.start_time),
            "end": str(time_slot.end_time)
        } if time_slot else None,

        # 🔥 SCHEDULE (dars kunlari)
        "schedule": group.schedule if group else None,

        "coins": coins,

        "level": {
            "name": level["name"],
            "image": level["image"],
            "next_level": level["next_level"],
            "next_level_coins": level["next_level_coins"],
            "progress_percent": level["progress_percent"]
        }
    }


@router.get("/me/attendance")
def my_attendance(
    current_student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return get_student_attendance(
        db,
        current_student.id
    )


@router.post("/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return upload_student_avatar(
        db=db,
        student=current_student,
        file=file
    )


@router.get("/coins/history")
def coin_history(
    current_student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    transactions = db.query(CoinTransaction).options(
        joinedload(CoinTransaction.teacher)
    ).filter(
        CoinTransaction.student_id == current_student.id
    ).order_by(
        CoinTransaction.created_at.desc()
    ).all()

    return [
        {
            "amount": t.amount,
            "type": t.type.value,  # 🔥 MUHIM
            "date": t.created_at.replace(
                tzinfo=pytz.utc
            ).astimezone(UZ_TZ).strftime("%Y-%m-%d %H:%M"),
            "teacher": t.teacher.full_name if t.teacher else None,
            "comment": t.comment
        }
        for t in transactions
    ]


@router.get("/leaderboard")
def leaderboard(
    period: str,
    db: Session = Depends(get_db)
):
    return get_global_leaderboard(db, period)


@router.get("/group-leaderboard")
def group_leaderboard(
    period: str,
    current_student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return get_group_leaderboard(
        db,
        current_student,
        period
    )


@router.get("/")
def get_students(
    search: str = None,
    group_name: str = None,
    is_active: bool = None,
    status: str = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    # 🔥 explicit join
    query = db.query(Student).outerjoin(
        Group,
        Student.group_id == Group.id
    )

    # 🔍 search
    if search:
        query = query.filter(
            Student.full_name.ilike(f"%{search}%")
        )

    # 🏫 group filter
    if group_name:
        query = query.filter(
            Group.name.ilike(f"%{group_name}%")
        )

    # ✅ active filter
    if is_active is not None:
        query = query.filter(
            Student.is_active == is_active
        )

    # 🔥 status filter
    if status:
        allowed_statuses = [
            "active",
            "frozen",
            "archived",
            "graduated"
        ]

        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid status"
            )

        query = query.filter(
            Student.status == status
        )

    students = query.offset(skip).limit(limit).all()

    return {
        "total": query.count(),
        "data": students
    }


@router.post("/{student_id}/notes")
def add_student_note(
    student_id: int,
    data: StudentNoteCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    note = StudentNote(
        student_id=student.id,
        admin_id=user.id,
        text=data.text
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "message": "Note added"
    }


@router.get("/{student_id}/notes")
def student_notes(
    student_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    notes = db.query(StudentNote).filter(
        StudentNote.student_id == student_id
    ).order_by(
        StudentNote.created_at.desc()
    ).all()

    return [
        {
            "id": n.id,
            "text": n.text,

            "admin": {
                "id": n.admin.id,
                "full_name": n.admin.full_name
            },

            "created_at": n.created_at.strftime("%d.%m.%Y | %H:%M")
        }
        for n in notes
    ]


@router.post("/")
def create(
    data: StudentCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))  # 🔥 faqat admin
):
    return create_student(db, data)


@router.get("/{student_id}/profile")
def get_student_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin", "teacher"))
):
    student = db.query(Student).get(student_id)

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user.role == "teacher":
        if student.group.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your student")

    return student



@router.get("/{student_id}/card")
def generate_student_card(
    student_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    pdf_bytes = generate_card_pdf(
        full_name=student.full_name,
        student_id=student.student_code,
        password=student.plain_password,
        code=f"ID: {student.student_code}\nPassword: {student.plain_password}"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=card_{student.student_code}.pdf"
        }
    )



@router.post("/{student_id}/reset-password")
def reset_password(
    student_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_role("admin"))
):

    return reset_student_password(
        db,
        student_id
    )


@router.put("/assign-group")
def assign_group(
    student_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    # 🔥 eski history yopamiz
    last_history = db.query(StudentGroupHistory).filter(
        StudentGroupHistory.student_id == student_id,
        StudentGroupHistory.end_date == None
    ).first()

    if last_history:
        last_history.end_date = date.today()

    # 🔥 yangi history ochamiz
    new_history = StudentGroupHistory(
        student_id=student_id,
        group_id=group_id,
        start_date=date.today()
    )

    # 🔥 studentni yangilaymiz (current state)
    student.group_id = group_id

    db.add(new_history)
    db.commit()
    db.refresh(student)

    return {
        "message": "Student moved successfully",
        "student_id": student.id,
        "new_group_id": group_id
    }


@router.post("/transfer-students")
def transfer_students(
    from_group_id: int,
    to_group_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    from_group = db.query(Group).filter(
        Group.id == from_group_id
    ).first()

    to_group = db.query(Group).filter(
        Group.id == to_group_id
    ).first()

    if not from_group or not to_group:
        raise HTTPException(404, "Group not found")

    students = db.query(Student).filter(
        Student.group_id == from_group_id,
        Student.is_active == True
    ).all()

    transferred = []

    for student in students:

        # 🔥 old history close
        last_history = db.query(StudentGroupHistory).filter(
            StudentGroupHistory.student_id == student.id,
            StudentGroupHistory.end_date == None
        ).first()

        if last_history:
            last_history.end_date = date.today()

        # 🔥 new history
        new_history = StudentGroupHistory(
            student_id=student.id,
            group_id=to_group_id,
            start_date=date.today()
        )

        student.last_group_id = student.group_id
        student.group_id = to_group_id

        db.add(new_history)

        transferred.append({
            "student_id": student.id,
            "student_name": student.full_name
        })

    db.commit()

    return {
        "message": "Students transferred successfully",
        "from_group": from_group.name,
        "to_group": to_group.name,
        "students_count": len(transferred),
        "students": transferred
    }


@router.get("/balance/{student_id}")
def balance(
    student_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return get_student_balance(db, student_id)


@router.put("/{student_id}")
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    student = update_student_service(db, student_id, data)

    return {
        "message": "Student updated",
        "data": student
    }


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))  # 🔥 faqat admin
):
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()

    return {
        "message": "Student deleted"
    }


@router.get("/status/{status}")
def get_students_by_status(
    status: str,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    students = db.query(Student).filter(
        Student.status == status
    ).all()

    return students


@router.patch("/{student_id}/status")
def update_student_status(
    student_id: int,
    data: StudentStatusUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    allowed_statuses = [
        "active",
        "frozen",
        "archived",
        "transferred",
        "graduated"
    ]

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    old_status = student.status

    # 🔥 status update
    student.status = data.status
    student.status_reason = data.reason

    # 🔥 only active students active bo‘ladi
    student.is_active = data.status == "active"

    today = date.today()

    # =====================================================
    # 🔥 GROUPDAN CHIQARISH
    # =====================================================

    removable_statuses = [
        "archived",
        "transferred",
        "graduated"
    ]

    if data.status in removable_statuses:

        active_history = db.query(StudentGroupHistory).filter(
            StudentGroupHistory.student_id == student.id,
            StudentGroupHistory.end_date == None
        ).first()

        if active_history:

            # 🔥 keyin qaytarish uchun group eslab qolamiz
            student.last_group_id = active_history.group_id

            # 🔥 history yopiladi
            active_history.end_date = today

            # 🔥 groupdan chiqariladi
            student.group_id = None

    # =====================================================
    # 🔥 ACTIVE QAYTSA
    # =====================================================

    if data.status == "active":

        # 🔥 oldin groupi bo‘lganmi
        if student.last_group_id:

            existing_history = db.query(StudentGroupHistory).filter(
                StudentGroupHistory.student_id == student.id,
                StudentGroupHistory.group_id == student.last_group_id,
                StudentGroupHistory.end_date == None
            ).first()

            # 🔥 duplicate bo‘lmasin
            if not existing_history:

                new_history = StudentGroupHistory(
                    student_id=student.id,
                    group_id=student.last_group_id,
                    start_date=today
                )

                db.add(new_history)

            student.group_id = student.last_group_id

    # =====================================================
    # 🔥 HISTORY SAVE
    # =====================================================

    history = StudentStatusHistory(
        student_id=student.id,
        changed_by=user.id,
        status=data.status,
        reason=data.reason,
        changed_at=datetime.utcnow()
    )

    db.add(history)

    db.commit()
    db.refresh(student)

    return {
        "message": "Student status updated",

        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "status": student.status,
            "status_reason": student.status_reason,
            "is_active": student.is_active,
            "group_id": student.group_id
        }
    }


@router.get("/{student_id}/status-history")
def get_status_history(
    student_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    history = db.query(StudentStatusHistory).filter(
        StudentStatusHistory.student_id == student_id
    ).order_by(StudentStatusHistory.changed_at.desc()).all()

    return history

