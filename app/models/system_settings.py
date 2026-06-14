from sqlalchemy import Column, Integer, Float
from app.db.base import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True)

    # 🔥 salary tax percent
    tax_percent = Column(Float, default=7.5)