from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func
from fastapi import HTTPException
from app.models.group import Group
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.models.holiday import Holiday
from app.models.student import Student
from sqlalchemy.orm import Session, joinedload




def create_payment(db: Session, data, current_user):

    student = db.query(Student).filter(
        Student.id == data.student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    if not student.is_active:
        raise HTTPException(400, "Student is inactive")

    if not student.group_id:
        raise HTTPException(400, "Student not assigned to group")

    group = db.query(Group).filter(
        Group.id == student.group_id
    ).first()

    if not group:
        raise HTTPException(404, "Group not found")

    # 🔥 PAYMENT DATE FIX
    payment_date = data.payment_date or date.today()

    # 🔥 DECIMAL FIX
    total_paid = db.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.student_id == student.id,
        Payment.month == data.month
    ).scalar()

    total_paid = Decimal(total_paid)
    amount = Decimal(data.amount)
    group_price = Decimal(group.price)

    # 🔥 GROUP LESSON DAYS
    lesson_dates = []

    current_date = payment_date.replace(day=1)

    while current_date.month == payment_date.month:

        weekday = current_date.weekday()

        if weekday in group.schedule:
            lesson_dates.append(current_date)

        current_date += timedelta(days=1)

    # 🔥 UNPAID HOLIDAYS
    unpaid_holidays = db.query(Holiday).filter(
        Holiday.date.in_(lesson_dates),
        Holiday.is_paid == False
    ).all()

    holiday_dates = [h.date for h in unpaid_holidays]

    # 🔥 REAL LESSON COUNT
    real_lessons = len([
        d for d in lesson_dates
        if d not in holiday_dates
    ])

    all_lessons = len(lesson_dates)

    # 🔥 PER LESSON PRICE
    lesson_price = group_price / all_lessons

    # 🔥 REAL MONTH PRICE
    real_month_price = lesson_price * real_lessons

    # 🔥 OVERPAYMENT CHECK
    if total_paid + amount > real_month_price:
        raise HTTPException(
            400,
            f"Payment exceeds monthly fee. Already paid: {total_paid}"
        )

    # 🔥 CREATE
    payment = Payment(
        student_id=student.id,
        group_id=group.id,
        amount=amount,
        month=data.month,
        payment_date=payment_date,

        payment_method=data.payment_method,
        created_by=current_user.id,
        comment=data.comment
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "message": "Payment added",
        "paid_now": amount,
        "total_paid": total_paid + amount,
        "remaining": real_month_price - (total_paid + amount)
    }


def get_debtors(db: Session):
    students = db.query(Student).options(
        joinedload(Student.group),
        joinedload(Student.payments)
    ).all()

    result = []

    for student in students:
        total_paid = sum(p.amount for p in student.payments)

        group_price = student.group.price if student.group else 0

        debt = group_price - total_paid

        if debt > 0:
            result.append({
                "student_id": student.id,
                "full_name": student.full_name,
                "group": student.group.name if student.group else None,
                "group_price": group_price,
                "paid": total_paid,
                "debt": debt
            })

    return result


def check_month_payment(db: Session, student_id: int, month: str):
    payments = db.query(Payment).filter(
        Payment.student_id == student_id,
        Payment.month == month
    ).all()

    total = sum(p.amount for p in payments)

    return {
        "student_id": student_id,
        "month": month,
        "paid": total
    }


def get_payment_status(db: Session, student_id: int):
    student = db.query(Student).options(joinedload(Student.group)).filter(
        Student.id == student_id
    ).first()

    payments = student.payments

    total_paid = sum(p.amount for p in payments)

    group_price = student.group.price if student.group else 0

    debt = group_price - total_paid

    percentage = int((total_paid / group_price) * 100) if group_price > 0 else 0

    return {
        "student_id": student_id,
        "group_price": group_price,
        "paid": total_paid,
        "debt": debt,
        "percentage": percentage
    }


def get_today_cash(db: Session):
    today = date.today()

    payments = db.query(
        Payment.payment_method,
        func.coalesce(func.sum(Payment.amount), 0).label("total"),
        func.count(Payment.id).label("count")
    ).filter(
        Payment.payment_date == today
    ).group_by(
        Payment.payment_method
    ).all()

    result = {
        "cash": Decimal(0),
        "card": Decimal(0),
        "total": Decimal(0),
        "payments_count": 0
    }

    for p in payments:
        method = p.payment_method
        amount = Decimal(p.total)

        result[method] = amount
        result["total"] += amount
        result["payments_count"] += p.count

    return result


def get_cash_analytics(db: Session, from_date: date, to_date: date):
    payments = db.query(
        Payment.payment_method,
        func.coalesce(func.sum(Payment.amount), 0).label("total"),
        func.count(Payment.id).label("count")
    ).filter(
        Payment.payment_date >= from_date,
        Payment.payment_date <= to_date
    ).group_by(
        Payment.payment_method
    ).all()

    result = {
        "cash": Decimal(0),
        "card": Decimal(0),
        "total": Decimal(0),
        "payments_count": 0
    }

    for p in payments:
        method = p.payment_method
        amount = Decimal(p.total)

        result[method] = amount
        result["total"] += amount
        result["payments_count"] += p.count

    return result


def get_daily_analytics(db: Session, from_date: date, to_date: date):
    payments = db.query(
        Payment.payment_date,
        func.sum(Payment.amount).label("total")
    ).filter(
        Payment.payment_date >= from_date,
        Payment.payment_date <= to_date,
        Payment.status == "paid"
    ).group_by(Payment.payment_date).order_by(Payment.payment_date).all()

    result = []

    for p in payments:
        result.append({
            "date": p.payment_date,
            "total": float(p.total)
        })

    return result


def get_monthly_analytics(db: Session, year: int):
    payments = db.query(
        func.substr(Payment.month, 1, 7).label("month"),
        func.sum(Payment.amount).label("total")
    ).filter(
        Payment.status == "paid"
    ).group_by("month").order_by("month").all()

    result = []

    for p in payments:
        result.append({
            "month": p.month,
            "total": float(p.total)
        })

    return result

