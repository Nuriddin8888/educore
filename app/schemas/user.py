from pydantic import BaseModel, constr

class UserCreate(BaseModel):
    full_name: str
    phone_number: constr(min_length=9, max_length=15)
    password: constr(min_length=6)
    email: str | None = None  # optional
    role: str | None = "student"

class UserLogin(BaseModel):
    phone_number: str
    password: str

    