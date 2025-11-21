from pydantic import BaseModel,  EmailStr, ConfigDict
from datetime import date, time, datetime

class DoctorCreate(BaseModel):
    user_id: int
    name: str
    specialization: str | None = None
    qualification: str | None = None
    position: str | None = None
    dob: date | None = None
    chamber: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    consultation_fee: int | None = None

class DoctorAdminCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    specialization: str | None = None
    qualification: str | None = None
    position: str | None = None
    dob: date | None = None
    chamber: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    consultation_fee: int | None = None

class DoctorUpdate(BaseModel):
    name: str | None = None
    specialization: str | None = None
    qualification: str | None = None
    position: str | None = None
    dob: date | None = None
    chamber: str | None = None
    start_time: time | None = None
    end_time: time | None = None

class DoctorOut(BaseModel):
    id: int
    name: str
    specialization: str | None
    qualification: str | None
    position: str | None
    status: str | None
    consultation_fee: int | None

    class Config:
        from_attributes = True

class DoctorAdminUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None
    specialization: str | None = None
    qualification: str | None = None
    position: str | None = None
    dob: date | None = None
    chamber: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    consultation_fee: int | None = None
    status: bool | None = None

class DoctorResponse(BaseModel):
    id: int
    name: str
    specialization: str | None
    position: str | None
    consultation_fee: int | None
    status: bool

    class Config:
        from_attributes = True

class DoctorPublicResponse(BaseModel):
    id: int
    name: str
    specialization: str
    chamber: str | None = None

    model_config = ConfigDict(from_attributes=True)

class DoctorAdminResponse(BaseModel):
    id: int
    name: str
    email: str
    specialization: str
    qualification: str | None = None
    position: str | None = None
    chamber: str | None = None
    status: bool
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None

    model_config = ConfigDict(from_attributes=True)