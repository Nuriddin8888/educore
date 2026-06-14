from app.db.base import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime



class StudentStatusHistory(Base):
    __tablename__ = "student_status_history"

    id = Column(Integer, primary_key=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    changed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    status = Column(
        String,
        nullable=False
    )

    reason = Column(
        String,
        nullable=True
    )

    changed_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    student = relationship(
        "Student",
        backref="status_history"
    )

    admin = relationship("User")