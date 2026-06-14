from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from app.db.base import Base


class TeacherSalary(Base):
    __tablename__ = "teacher_salaries"

    id = Column(Integer, primary_key=True)

    teacher_id = Column(Integer, ForeignKey("users.id"))
    month = Column(String)  # "2026-03"

    total_salary = Column(Numeric(10, 2))

    created_at = Column(DateTime)

    teacher = relationship("User")