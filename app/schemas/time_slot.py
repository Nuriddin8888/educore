from datetime import time
from pydantic import BaseModel, Field, field_validator, ValidationInfo


class TimeSlotBase(BaseModel):
    start_time: time = Field(example="07:00")
    end_time: time = Field(example="09:00")

    @field_validator("end_time")
    def check_time(cls, v, info: ValidationInfo):
        start_time = info.data.get("start_time")

        if start_time is None:
            return v

        if v <= start_time:
            raise ValueError("End time must be greater than start time")

        return v


class TimeSlotCreate(TimeSlotBase):
    pass


class TimeResponse(BaseModel):
    id: int
    start: time = Field(alias="start_time")
    end: time = Field(alias="end_time")

    class Config:
        from_attributes = True
        populate_by_name = True
