# models/student.py
from app.db.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean



class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True)

    gender = Column(String)
    birth_date = Column(Date)

    parent_phone = Column(String)
    address = Column(String)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group",back_populates="students",foreign_keys=[group_id])
    is_active = Column(Boolean, default=True)
    status = Column(String, default="active")
    status_reason = Column(String, nullable=True)
    attendances = relationship("Attendance", backref="student")
    payments = relationship("Payment", back_populates="student")
    coin_transactions = relationship("CoinTransaction", back_populates="student")
    coin = relationship("StudentCoin", uselist=False, back_populates="student")
    last_group_id = Column(Integer, ForeignKey("groups.id"),nullable=True)
    last_group = relationship("Group",foreign_keys=[last_group_id])

    student_code = Column(String, unique=True, index=True)  # login ID
    password = Column(String)  # hashed password
    plain_password = Column(String)
    avatar = Column(String, nullable=True, default="default.png")