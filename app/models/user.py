from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=False)
    role = Column(String, default="teacher")
    grade_id = Column(Integer, ForeignKey("teacher_grades.id"))
    grade_rel = relationship("TeacherGrade", back_populates="teachers")
    teacher_coin = relationship("TeacherCoin", back_populates="teacher", uselist=False)
    coin_transactions = relationship("CoinTransaction", back_populates="teacher")
    face_enabled = Column(Boolean, default=False)
    face_embedding = Column(JSON, nullable=True)




