from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.config.auth import RoleChecker, verify_token, get_password_hash
from app.models import models
from app.schemas.doctor_schema import DoctorAdminCreate, DoctorAdminUpdate

router = APIRouter(prefix="/admin", tags=["Admin"])

# 1. ADMIN DASHBOARD
@router.get("/dashboard", dependencies=[Depends(RoleChecker(["admin"]))])
def get_admin_dashboard(db: Session = Depends(get_db)):

    total_doctors = db.query(models.Doctor).filter(models.Doctor.deleted_at.is_(None)).count()
    total_users = db.query(models.User).count()
    total_appointments = db.query(models.Appointment).count()

    return {
        "total_doctors": total_doctors,
        "total_users": total_users,
        "total_appointments": total_appointments
    }

# 2. CREATE DOCTOR (ADMIN)
@router.post("/create", dependencies=[Depends(RoleChecker(["admin"]))])
def create_doctor_admin(payload: DoctorAdminCreate, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    user = models.User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Assign doctor role
    doctor_role = db.query(models.Role).filter(models.Role.name == "doctor").first()
    if not doctor_role:
        doctor_role = models.Role(name="doctor", created_at=datetime.utcnow())
        db.add(doctor_role)
        db.commit()
        db.refresh(doctor_role)

    user_role = models.UserRole(user_id=user.id, role_id=doctor_role.id)
    db.add(user_role)
    db.commit()

    # Create doctor profile
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

# 3. LIST DOCTORS (ADMIN)
@router.get("/")
def list_doctors(
    specialization: Optional[str] = None,
    status: Optional[bool] = None,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token)
):
    user_role = payload.get("role")

    # Base query
    query = db.query(models.Doctor)

    # Filter by specialization
    if specialization:
        query = query.filter(models.Doctor.specialization.ilike(f"%{specialization}%"))

    if user_role == "admin":
        if status is not None:  # admin can filter status
            query = query.filter(models.Doctor.status == status)

    doctors = query.all()

    # Convert to JSON-friendly response
    return [
        {
            "id": d.id,
            "name": d.name,
            "specialization": d.specialization,
            "status": d.status,
            "deleted_at": d.deleted_at
        }
        for d in doctors
    ]

# 4. GET SINGLE DOCTOR (VIEW BUTTON)
@router.get("/doctor/email/{email}", dependencies=[Depends(RoleChecker(["admin"]))])
def get_doctor_by_email(email: str, db: Session = Depends(get_db)):

    doctor = (
        db.query(models.Doctor)
        .join(models.User, models.Doctor.user_id == models.User.id)
        .filter(models.User.email == email)
        .first()
    )

    if not doctor:
        raise HTTPException(404, "Doctor not found")

    return {
        "id": doctor.id,
        "name": doctor.name,
        "email": doctor.user.email,  # <-- email comes from User table
        "specialization": doctor.specialization,
        "qualification": doctor.qualification,
        "position": doctor.position,
        "dob": doctor.dob,
        "chamber": doctor.chamber,
        "start_time": doctor.start_time,
        "end_time": doctor.end_time,
        "status": doctor.status,
        "consultation_fee": doctor.consultation_fee
    }

# 5. UPDATE DOCTOR (ADMIN)
@router.patch("/doctor/update/{doctor_id}", dependencies=[Depends(RoleChecker(["admin"]))])
def update_doctor(doctor_id: int, payload: DoctorAdminUpdate, db: Session = Depends(get_db)):

    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")

    # Update only the fields provided
    update_data = payload.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(doctor, field, value)

    doctor.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(doctor)

    return {"message": "Doctor updated successfully", "doctor_id": doctor.id}


# 6. DELETE DOCTOR (SOFT DELETE)
@router.patch("/doctor/delete/{doctor_id}", dependencies=[Depends(RoleChecker(["admin"]))])
def soft_delete_doctor(doctor_id: int, db: Session = Depends(get_db)):

    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")

    if doctor.deleted_at:
        return {"message": "Doctor already deleted"}

    doctor.deleted_at = datetime.utcnow()
    doctor.status = False
    db.commit()

    return {"message": "Doctor deleted successfully", "doctor_id": doctor_id}