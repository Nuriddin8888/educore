from pydantic import BaseModel
from datetime import date
from typing import Optional
from app.schemas.time_slot import TimeResponse



class GroupCreate(BaseModel):
    course_name: str
    teacher_id: int
    price: int
    start_date: date
    schedule: list[int]
    room_id: int
    time_slot_id: int



class StudentMini(BaseModel):
    id: int
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True



class GroupDetailResponse(BaseModel):
    group_id: int
    name: str
    course: str
    students_count: int

    room: RoomResponse | None
    time: TimeResponse | None
    schedule: list[int]

    students: list[StudentMini]

    class Config:
        from_attributes = True



class TeacherMini(BaseModel):
    id: int
    full_name: str

    class Config:
        from_attributes = True



class GroupUpdate(BaseModel):
    teacher_id: Optional[int] = None
    price: Optional[int] = None
    schedule: Optional[list] = None
    is_active: Optional[bool] = None
    time_slot_id: Optional[int] = None   # 🔥 qo‘shamiz
    room_id: Optional[int] = None  


# 🔥 ROOM
class RoomResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# 🔥 TIME
# class TimeResponse(BaseModel):
#     start: Optional[str]
#     end: Optional[str]



# 🔥 GROUP DETAIL
# class GroupDetailResponse(BaseModel):
#     group_id: int
#     name: str
#     course: str
#     students_count: int

#     room: Optional[RoomResponse]
#     time: TimeResponse
#     schedule: List[int]

#     students: List[StudentMini]