from app.db.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey



class TeacherCoin(Base):
    __tablename__ = "teacher_coins"

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), unique=True)
    balance = Column(Integer, default=0)

    teacher = relationship("User", back_populates="teacher_coin")