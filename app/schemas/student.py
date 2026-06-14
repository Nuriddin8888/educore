from pydantic import BaseModel
from datetime import date
from typing import Optional


class StudentLogin(BaseModel):
    student_code: str
    password: str


class ChangeStudentPassword(BaseModel):
    old_password: str
    new_password: str


class StudentCreate(BaseModel):
    full_name: str
    phone_number: str
    gender: str
    birth_date: date
    parent_phone: str | None = None
    address: str | None = None
    group_id: Optional[int] = None


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    parent_phone: Optional[str] = None
    address: Optional[str] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = None



class StudentStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None


class StudentNoteCreate(BaseModel):
    text: str