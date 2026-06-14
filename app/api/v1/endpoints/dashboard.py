import pytz
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.core.deps import get_db, require_role
from app.schemas.salary import PaymentCalculateRequest
from app.schemas.system import TaxUpdate
from app.services.dashboard_service import get_dashboard, get_advanced_dashboard, calculate_student_payment, get_groups_schedule_dashboard, remove_holiday, get_group_calendar
from app.schemas.holiday import HolidayCreate
from app.models.holiday import Holiday
from app.models.system_settings import SystemSettings

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
UZ_TZ = pytz.timezone("Asia/Tashkent")


@router.post("/calculate")
def calculate_payment(
    data: PaymentCalculateRequest,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin"))
):

    return calculate_student_payment(
        db=db,
        group_id=data.group_id,
        join_date=data.join_date
    )


@router.get("/")
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard(db)


@router.get("/advanced")
def advanced_dashboard(db: Session = Depends(get_db)):
    return get_advanced_dashboard(db)


@router.get("/holidays")
def get_holidays(
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    holidays = db.query(Holiday).order_by(Holiday.date).all()

    return [
        {
            "id": h.id,
            "name": h.name,
            "created_by": h.created_by,
            "date": str(h.date),
            "is_paid": h.is_paid,
            "description": h.description,
            "created_at": h.created_at.replace(
                tzinfo=pytz.utc
            ).astimezone(UZ_TZ).strftime("%Y-%m-%d %H:%M"),
        }
        for h in holidays
    ]


@router.post("/holidays")
def create_holiday(
    data: HolidayCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    holiday = Holiday(
        name=data.name,
        date=data.date,
        created_by=user.id,
        description=data.description
    )

    db.add(holiday)
    db.commit()

    return {
        "message": "Holiday created"
    }


@router.delete("/{holiday_id}")
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return remove_holiday(db, holiday_id)


@router.get("/groups-schedule")
def groups_schedule_dashboard(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):

    return get_groups_schedule_dashboard(db, type)


@router.get("/{group_id}/calendar")
def group_calendar(
    group_id: int,
    month: str,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return get_group_calendar(db, group_id, month)


@router.put("/tax")
def update_tax(
    data: TaxUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    settings = db.query(SystemSettings).first()

    if not settings:
        settings = SystemSettings()

    settings.tax_percent = data.tax_percent

    db.add(settings)
    db.commit()

    return {
        "message": "Tax updated",
        "tax_percent": settings.tax_percent
    }


