import enum
from sqlalchemy import Enum
from app.db.base import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime



class CoinTypeEnum(str, enum.Enum):
    attendance = "attendance"
    bonus = "bonus"
    monthly_bonus = "monthly_bonus"
    manual_add = "manual_add"
    manual_subtract = "manual_subtract"



class CoinTransaction(Base):
    __tablename__ = "coin_transactions"

    id = Column(Integer, primary_key=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    amount = Column(Integer)  # +2, -1, +100

    type = Column(Enum(CoinTypeEnum), nullable=False)
    # attendance | bonus | manual_add | manual_subtract

    created_at = Column(DateTime, default=datetime.utcnow)

    comment = Column(String, nullable=True)

    student = relationship("Student", back_populates="coin_transactions")
    teacher = relationship("User", back_populates="coin_transactions")