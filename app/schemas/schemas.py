from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from app.enums.gender import GenderEnum


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    gender: GenderEnum
    dob: date
    blood_group: Optional[str] = None

    model_config = {"from_attributes": True}



class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    role: str

    model_config = {"from_attributes": True}

    
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes = True
