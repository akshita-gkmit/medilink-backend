from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import models
from app.schemas import schemas
from app.db.database import get_db
from app.config.auth import get_password_hash, verify_password, create_access_token, create_refresh_token, verify_token
from datetime import datetime

router = APIRouter(prefix="/auth")

# 1. Creates a new user account with 'patient' role and patient profile.
@router.post("/register", response_model=schemas.UserResponse)
def register_user(request: schemas.RegisterRequest, db: Session = Depends(get_db)):
   
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = models.User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
   
    role = db.query(models.Role).filter(models.Role.name == "patient").first()
    if not role:
        role = models.Role(name="patient", created_at=datetime.utcnow())
        db.add(role)
        db.commit()
        db.refresh(role)

    user_role = models.UserRole(user_id=user.id, role_id=role.id)
    db.add(user_role)
    db.commit()

    patient = models.Patient(
        user_id=user.id,
        name=request.name,
        gender=request.gender,
        dob=request.dob,
        blood_group=request.blood_group,
        created_at=datetime.utcnow()
    )
    db.add(patient)
    db.commit()

    return {"id": user.id, "email": user.email, "role": "patient"}

# 2. Verifies credentials and returns JWT access & refresh tokens with role-based info.
@router.post("/login", response_model=schemas.TokenResponse)
def login_user(request: schemas.LoginRequest, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_role = (
        db.query(models.Role.name)
        .join(models.UserRole, models.UserRole.role_id == models.Role.id)
        .filter(models.UserRole.user_id == user.id)
        .first()
    )

    role_name = user_role[0]

    doctor_id = None
    doctor_name = None

    # If user is doctor → fetch doctor profile
    if role_name.lower() == "doctor":
        doctor = db.query(models.Doctor).filter(models.Doctor.user_id == user.id).first()
        if doctor:
            doctor_id = doctor.id
            doctor_name = doctor.name

    # If user is patient → fetch patient name
    patient_name = None
    if role_name.lower() == "patient":
        patient = db.query(models.Patient).filter(models.Patient.user_id == user.id).first()
        if patient:
            patient_name = patient.name

    # Token payload
    payload = {
        "sub": user.email,
        "user_id": user.id,
        "role": role_name,
        "doctor_id": doctor_id
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "email": user.email,
        "role": role_name,
        "userId": user.id,
        "doctorId": doctor_id,
        "name": doctor_name if doctor_name else patient_name
    }

# 3. Confirms token validity and returns user identity + role profile details.
@router.get("/validate-token")
def validate_token(payload = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload.get("user_id")
    role = payload.get("role")

    user = db.query(models.User).filter(models.User.id == user_id).first()

    doctor_id = None
    doctor_name = None

    if role.lower() == "doctor":
        doctor = db.query(models.Doctor).filter(models.Doctor.user_id == user_id).first()
        if doctor:
            doctor_id = doctor.id
            doctor_name = doctor.name

    patient_name = None
    if role.lower() == "patient":
        patient = db.query(models.Patient).filter(models.Patient.user_id == user_id).first()
        if patient:
            patient_name = patient.name

    return {
        "email": user.email,
        "role": role,
        "userId": user_id,     
        "doctorId": doctor_id, 
        "name": doctor_name if doctor_name else patient_name
    }
