from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    gender: str # "male" | "female" | "other"
    dob: date
    blood_group: Optional[str] = None

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    login_as: str  # "patient" | "doctor" | "admin"

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    role: str

    class Config:
        orm_mode = True

    
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes = True
