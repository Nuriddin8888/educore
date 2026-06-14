from pydantic import BaseModel
from datetime import date
from app.core.enums import AttendanceStatus


class AttendanceCreate(BaseModel):
    student_id: int
    group_id: int
    date: date
    status: AttendanceStatus