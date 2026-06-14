from enum import Enum
from typing import Optional
from pydantic import BaseModel


class TeacherCreate(BaseModel):
    full_name: str
    phone_number: str
    password: str
    email: str | None = None
    

class ChangePassword(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None



class CoinAction(str, Enum):
    add = "add"
    subtract = "subtract"


class TeacherCoinAction(BaseModel):
    student_id: int
    amount: int
    action: CoinAction
    comment: Optional[str] = None