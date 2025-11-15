from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.auth import RoleChecker, verify_token
from typing import Optional
from app.db.database import get_db
from app.config.auth import get_password_hash
from app.models import models
from app.schemas.doctor_schema import DoctorAdminCreate, DoctorAdminUpdate
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard", dependencies=[Depends(RoleChecker(["admin"]))])
def get_admin_dashboard():
    return {"status": "Admin dashboard working!"}

@router.post("/create", dependencies=[Depends(RoleChecker(["admin"]))])
def create_doctor_admin(payload: DoctorAdminCreate, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = models.User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    doctor_role = db.query(models.Role).filter(models.Role.name == "doctor").first()
    if not doctor_role:
        doctor_role = models.Role(name="doctor", created_at=datetime.utcnow())
        db.add(doctor_role)
        db.commit()
        db.refresh(doctor_role)

    user_role = models.UserRole(user_id=user.id, role_id=doctor_role.id)
    db.add(user_role)
    db.commit()

    doctor = models.Doctor(
        user_id=user.id,
        name=payload.name,
        specialization=payload.specialization,
        qualification=payload.qualification,
        position=payload.position,
        dob=payload.dob,
        chamber=payload.chamber,
        start_time=payload.start_time,
        end_time=payload.end_time,
        consultation_fee=payload.consultation_fee,
        status=True
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return {"message": "Doctor created successfully", "doctor_id": doctor.id, "user_id": user.id}

