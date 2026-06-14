from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, JSON, Numeric
from app.db.base import Base



class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    course_name = Column(String, nullable=False)

    teacher_id = Column(Integer, ForeignKey("users.id"))
    teacher = relationship("User", backref="groups")

    price = Column(Numeric(10, 2))
    start_date = Column(Date)
    schedule = Column(JSON)
    is_active = Column(Boolean, default=True)
    students = relationship("Student", back_populates="group",foreign_keys="Student.group_id")
    attendances = relationship("Attendance", backref="group")

    time_slot_id = Column(Integer, ForeignKey("time_slots.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))

    time_slot = relationship("TimeSlot")
    room = relationship("Room")

    def __str__(self):
        return self.name