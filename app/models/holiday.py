from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey
from app.db.base import Base


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    date = Column(Date, nullable=False, unique=True)

    description = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    is_paid = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)