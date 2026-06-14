from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, Date
from app.db.base import Base


class GroupTeacherHistory(Base):
    __tablename__ = "group_teacher_history"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"))

    start_date = Column(Date)
    end_date = Column(Date, nullable=True)

    group = relationship("Group")
    teacher = relationship("User")