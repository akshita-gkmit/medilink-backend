from sqlalchemy import Column, Integer, String, Boolean, Date, Time, Text, ForeignKey, TIMESTAMP, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    roles = relationship("UserRole", back_populates="user")
    doctor = relationship("Doctor", uselist=False, back_populates="user")
    patient = relationship("Patient", uselist=False, back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    users = relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name = Column(String(100), nullable=False)
    gender = Column(String(10))
    dob = Column(Date)
    blood_group = Column(String(10))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="doctor")
    slots = relationship("Slot", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(20), nullable=False, default="Available", index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_doctor_date_status', "doctor_id", "date", "status"),
    )

    doctor = relationship("Doctor", back_populates="slots")
    appointments = relationship("Appointment", back_populates="slot")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="Pending")
    booked_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    reason_for_visit = Column(Text)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    slot = relationship("Slot", back_populates="appointments")
    prescription = relationship("Prescription", back_populates="appointment", uselist=False, cascade="all, delete-orphan")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="CASCADE"), index=True, nullable=False)
    diagnosis = Column(Text)
    consultation_details = Column(Text)
    doctor_notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    appointment = relationship("Appointment", back_populates="prescription")
