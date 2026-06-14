from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
from fastapi import HTTPException


from app.core.deps import get_db, require_role
from app.schemas.payment import PaymentCreate
from app.services.payment_service import create_payment, get_debtors, check_month_payment, get_today_cash, get_cash_analytics, get_daily_analytics, get_monthly_analytics

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/")
def create(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return create_payment(db, data, user)


@router.get("/today")
def today_cash(
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return get_today_cash(db)


@router.get("/analytics")
def payment_analytics(
    period: str = "today",  # today / week / month
    from_date: date = None,
    to_date: date = None,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    today = date.today()

    if period == "today":
        from_date = to_date = today

    elif period == "week":
        from_date = today - timedelta(days=7)
        to_date = today

    elif period == "month":
        from_date = today.replace(day=1)
        to_date = today

    elif period == "custom":
        if not from_date or not to_date:
            raise HTTPException(400, "from_date and to_date required")

    else:
        raise HTTPException(400, "Invalid period")

    return get_cash_analytics(db, from_date, to_date)


@router.get("/analytics/daily")
def daily_analytics(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return get_daily_analytics(db, from_date, to_date)


@router.get("/analytics/monthly")
def monthly_analytics(
    year: int,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return get_monthly_analytics(db, year)


@router.get("/debtors")
def debtors(
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return get_debtors(db)


@router.get("/month-check")
def month_check(
    student_id: int,
    month: str,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin"))
):
    return check_month_payment(db, student_id, month)


