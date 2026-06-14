from pydantic import BaseModel
from datetime import date

class ReplacementCreate(BaseModel):
    group_id: int
    date: date
    replacement_teacher_id: int