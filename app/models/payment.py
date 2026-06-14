import enum
from app.db.base import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, Date, String, Numeric, Enum



class PaymentMethodEnum(str, enum.Enum):
    cash = "cash"
    card = "card"
    click = "click"
    payme = "payme"


class PaymentStatusEnum(str, enum.Enum):
    paid = "paid"
    cancelled = "cancelled"



class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))

    month = Column(String)
    amount = Column(Numeric, nullable=False)

    payment_date = Column(Date, server_default=func.current_date())

    payment_method = Column(Enum(PaymentMethodEnum), default=PaymentMethodEnum.cash, nullable=False)
    status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.paid, nullable=False)

    created_by = Column(Integer, ForeignKey("users.id"))
    comment = Column(String, nullable=True)

    student = relationship("Student", back_populates="payments")
    group = relationship("Group")
    created_by_user = relationship("User")