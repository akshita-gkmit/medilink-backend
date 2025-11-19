from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from app.enums.gender import GenderEnum

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    gender: str
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