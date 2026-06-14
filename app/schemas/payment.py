import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from enum import Enum

from pydantic import BaseModel

try:
    from pydantic import field_validator
    V2 = True
except ImportError:
    from pydantic import validator
    V2 = False


class PaymentMethod(str, Enum):
    cash = "cash"
    card = "card"
    transfer = "transfer"


class PaymentCreate(BaseModel):
    student_id: int
    amount: Decimal
    month: str
    payment_date: Optional[date] = None
    payment_method: PaymentMethod = PaymentMethod.cash
    comment: Optional[str] = None

    if V2:
        @field_validator("month")
        def validate_month(cls, v):
            try:
                dt = datetime.strptime(v, "%Y-%m")
                return dt.strftime("%Y-%m")
            except ValueError:
                raise ValueError("Month must be valid YYYY-MM format")

        @field_validator("amount")
        def validate_amount(cls, v):
            if v is None or v <= Decimal("0"):
                raise ValueError("Amount must be greater than 0")
            return v
    else:
        @validator("month")
        def validate_month(cls, v):
            try:
                dt = datetime.strptime(v, "%Y-%m")
                return dt.strftime("%Y-%m")
            except ValueError:
                raise ValueError("Month must be valid YYYY-MM format")

        @validator("amount")
        def validate_amount(cls, v):
            if v is None or v <= Decimal("0"):
                raise ValueError("Amount must be greater than 0")
            return v