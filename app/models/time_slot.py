from sqlalchemy import Column, Integer, Time
from app.db.base import Base



class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True)
    start_time = Column(Time)
    end_time = Column(Time)