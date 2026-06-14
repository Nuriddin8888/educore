from pydantic import BaseModel, Field


class GradeCreate(BaseModel):
    name: str
    price: int


class GradeUpdate(BaseModel):
    name: str | None = None
    price: int | None = None


class GradeResponse(BaseModel):
    id: int
    name: str
    price: int = Field(alias="price_per_lesson")

    class Config:
        from_attributes = True
        populate_by_name = True