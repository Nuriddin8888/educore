from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class StudentCoin(Base):
    __tablename__ = "student_coins"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True)
    balance = Column(Integer, default=0)

    student = relationship("Student", back_populates="coin")


