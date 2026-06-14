from pydantic import BaseModel
from datetime import datetime, date


class TeacherSalaryOut(BaseModel):
    id: int
    teacher_id: int
    teacher_name: str  # 🔥 yangi
    month: str
    total_salary: int
    created_at: datetime

    class Config:
        from_attributes = True  # orm_mode o‘rniga (Pydantic v2)

    # 🔥 formatlash
    @staticmethod
    def format_datetime(dt: datetime):
        return dt.strftime("%Y-%m-%d %H:%M")

    @classmethod
    def from_orm_with_format(cls, obj):
        return cls(
            id=obj.id,
            teacher_id=obj.teacher_id,
            teacher_name=obj.teacher.full_name,  # 🔥 shu qo‘shiladi
            month=obj.month,
            total_salary=obj.total_salary,
            created_at=cls.format_datetime(obj.created_at)
        )
    



class PaymentCalculateRequest(BaseModel):
    group_id: int
    join_date: date