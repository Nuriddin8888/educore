from sqlalchemy import Column, Integer, ForeignKey, Date
from app.db.base import Base


class StudentGroupHistory(Base):
    __tablename__ = "student_group_history"

    id = Column(Integer, primary_key=True)

    student_id = Column(Integer, ForeignKey("students.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))

    start_date = Column(Date)
    end_date = Column(Date, nullable=True)