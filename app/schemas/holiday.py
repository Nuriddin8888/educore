from pydantic import BaseModel
from datetime import date


class HolidayCreate(BaseModel):
    name: str
    date: date
    description: str | None = None