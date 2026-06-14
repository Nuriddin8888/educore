from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship

from app.db.base import Base


class TeacherGrade(Base):
    __tablename__ = "teacher_grades"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # junior, middle...
    price_per_lesson = Column(Numeric(10, 2))  # 🔥 asosiy narsa

    teachers = relationship("User", back_populates="grade_rel")