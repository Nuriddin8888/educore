from app.db.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, Date


class LessonReplacement(Base):
    __tablename__ = "lesson_replacements"

    id = Column(Integer, primary_key=True)

    group_id = Column(Integer,ForeignKey("groups.id"),nullable=False)

    original_teacher_id = Column(Integer,ForeignKey("users.id"),nullable=False)

    replacement_teacher_id = Column(Integer,ForeignKey("users.id"),nullable=False)

    date = Column(Date, nullable=False)

    # relationships
    group = relationship("Group",backref="replacements")

    original_teacher = relationship("User",foreign_keys=[original_teacher_id])

    replacement_teacher = relationship("User",foreign_keys=[replacement_teacher_id])