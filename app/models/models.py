from sqlalchemy import (
    Column, Integer, String, Boolean, Date, Time, Text,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.db.database import Base
from sqlalchemy import Enum as SAEnum
from app.enums.gender import GenderEnum

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    roles = relationship("UserRole", back_populates="user")
    doctor = relationship("Doctor", uselist=False, back_populates="user")
    patient = relationship("Patient", uselist=False, back_populates="user")

class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False)
    users = relationship("UserRole", back_populates="role")

class UserRole(BaseModel):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")

class Patient(BaseModel):
    __tablename__ = "patients"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name = Column(String(100), nullable=False)
    gender = Column(SAEnum(GenderEnum), nullable=True)
    dob = Column(Date)
    blood_group = Column(String(10))

    user = relationship("User", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")

class Doctor(BaseModel):
    __tablename__ = "doctors"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name = Column(String(100), nullable=False)
    specialization = Column(String(100))
    qualification = Column(String(100))
    position = Column(String(255))
    dob = Column(Date)
    chamber = Column(Text)
    start_time = Column(Time)
    end_time = Column(Time)
    consultation_fee = Column(Integer)
    status = Column(Boolean, default=True)

    user = relationship("User", back_populates="doctor")
    slots = relationship("Slot", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")

class Slot(BaseModel):   
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)   

    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(20), nullable=False, default="Available", index=True)

    __table_args__ = (
        Index("idx_doctor_date_status", "doctor_id", "date", "status"),
    )

    doctor = relationship("Doctor", back_populates="slots")
    appointments = relationship("Appointment", back_populates="slot")

class Appointment(BaseModel):
    __tablename__ = "appointments"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id", ondelete="CASCADE"), nullable=False)

    status = Column(String(20), default="Pending")
    booked_at = Column(Date)
    reason_for_visit = Column(Text)
    notes = Column(Text)

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    slot = relationship("Slot", back_populates="appointments")
    prescription = relationship("Prescription", back_populates="appointment", uselist=False, cascade="all, delete-orphan")

class Prescription(BaseModel):
    __tablename__ = "prescriptions"

    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="CASCADE"), index=True, nullable=False)
    diagnosis = Column(Text)
    consultation_details = Column(Text)
    doctor_notes = Column(Text)

    appointment = relationship("Appointment", back_populates="prescription")