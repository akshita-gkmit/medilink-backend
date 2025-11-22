from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date
from app.enums.gender import GenderEnum
import re

STRICT_EMAIL_REGEX = r"^[a-z0-9._%+-]+@[a-z]+\.[a-z]{2,6}$"


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    gender: str
    dob: date
    blood_group: Optional[str] = None

    @field_validator("email")
    def validate_email(cls, v):
        if not re.match(STRICT_EMAIL_REGEX, v):
            raise ValueError("Invalid email format")
        return v

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

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    slot_id: int
    reason_for_visit: str | None = None

class AppointmentStatusUpdate(BaseModel):
    appointment_id: int
    action: str 
    notes: str | None = None

class AppointmentCancel(BaseModel):
    appointment_id: int
    patient_id: int 

class BookAppointment(BaseModel):
    slot_id: int
    doctor_id: int
    patient_id: int

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
