from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import Response


from app.core.deps import get_db, require_role
from app.schemas.group import GroupCreate, GroupUpdate
from app.models.group import Group
from app.services.group_service import create_group, get_groups, get_group_detail, get_group_attendance, update_group_service, change_group_status_service, change_group_teacher
from app.utils.group_card import generate_group_pdf


from fastapi import HTTPException
from app.schemas.group import GroupDetailResponse

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("/")
def create(
    data: GroupCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return create_group(db, data)


@router.get("/")
def list_groups(
    search: str = None,        # 🔍 group name
    teacher_name: str = None,  # 🔥 teacher bo‘yicha filter
    course_name: str = None,   # 🔥 course bo‘yicha filter
    is_active: bool = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return get_groups(
        db,
        search,
        teacher_name,
        course_name,
        is_active,
        skip,
        limit
    )


@router.get("/{group_id}", response_model=GroupDetailResponse)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin", 'teacher'))
):
    group = get_group_detail(db, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return group


@router.get("/{group_id}/cards")
def generate_group_cards(
    group_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")

    students = [
        {
            "full_name": s.full_name,
            "student_id": s.student_code,
            "password": s.plain_password,
        }
        for s in group.students
    ]

    pdf_bytes = generate_group_pdf(
        group_name=group.name,
        teacher_name=group.teacher.full_name if group.teacher else "—",
        students=students,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=group_{group.name}.pdf"}
    )


@router.get("/group/{group_id}")
def group_attendance(
    group_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("teacher", "admin"))
):
    return get_group_attendance(db, group_id)


@router.put("/{group_id}")
def update_group(
    group_id: int,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    group = update_group_service(db, group_id, data)

    return {
        "message": "Group updated",
        "data": group
    }


@router.put("/{group_id}/change-teacher")
def change_teacher(
    group_id: int,
    new_teacher_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return change_group_teacher(db, group_id, new_teacher_id)


@router.patch("/{group_id}/status")
def change_group_status(
    group_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    group = change_group_status_service(db, group_id, is_active)

    return {
        "message": f"Group {'activated' if is_active else 'deactivated'}",
        "data": group
    }