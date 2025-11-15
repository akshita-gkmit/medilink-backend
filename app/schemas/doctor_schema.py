from pydantic import BaseModel,  EmailStr
from datetime import date, time

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
    chamber: str | None

    model_config = {
        "from_attributes": True
    }


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

