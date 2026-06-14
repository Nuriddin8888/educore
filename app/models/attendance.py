from app.db.base import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Date, UniqueConstraint, DateTime, Boolean
from app.core.constants import ATTENDANCE_UNCHECKED


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("students.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))

    date = Column(Date)

    status = Column(Integer, default=ATTENDANCE_UNCHECKED)  # present / absent
    teacher_id = Column(Integer, ForeignKey("users.id"))
    teacher = relationship("User")

    created_at = Column(DateTime, default=datetime.utcnow)
    lesson_start_time = Column(DateTime)
    lesson_price = Column(Integer, default=0)
    teacher_grade_name = Column(String, nullable=True)
    is_checked = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("student_id", "date", name="unique_student_day"),
    )
