from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from app.models import models
from app.schemas import schemas
from app.db.database import get_db
from app.config.auth import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, verify_token
)

router = APIRouter(prefix="/auth")

@router.post("/register", response_model=schemas.UserResponse)
def register_user(request: schemas.RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(models.User).filter(models.User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="Email already registered")

        user = models.User(
            email=request.email,
            password_hash=get_password_hash(request.password),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.flush()

        role = db.query(models.Role).filter(models.Role.name == "patient").first()
        if not role:
            role = models.Role(name="patient", created_at=datetime.utcnow())
            db.add(role)
            db.flush()

        user_role = models.UserRole(
            user_id=user.id,
            role_id=role.id,
            created_at=datetime.utcnow()
        )
        db.add(user_role)

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
        db.refresh(user)

        return {"id": user.id, "email": user.email, "role": "patient"}

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error:", str(e))
        raise HTTPException(status_code=500, detail="Database error during registration")

    except Exception as e:
        db.rollback()
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=schemas.TokenResponse)
def login_user(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.email == request.email).first()

        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_role = (
            db.query(models.Role.name)
            .join(models.UserRole, models.UserRole.role_id == models.Role.id)
            .filter(models.UserRole.user_id == user.id)
            .first()
        )

        if not user_role:
            raise HTTPException(status_code=400, detail="User has no assigned role")

        role_name = user_role[0].lower()

        doctor_id = None
        doctor_name = None
        patient_name = None

        if role_name == "doctor":
            doctor = db.query(models.Doctor).filter(models.Doctor.user_id == user.id).first()
            if doctor:
                doctor_id = doctor.id
                doctor_name = doctor.name

        if role_name == "patient":
            patient = db.query(models.Patient).filter(models.Patient.user_id == user.id).first()
            if patient:
                patient_name = patient.name

        payload = {
            "sub": user.email,
            "user_id": user.id,
            "role": role_name,
            "doctor_id": doctor_id  # ✅ SAFE now
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

    except HTTPException:
        raise

    except Exception as e:
        print("Login error:", str(e))
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/validate-token")
def validate_token(payload=Depends(verify_token), db: Session = Depends(get_db)):
    try:
        user_id = payload.get("user_id")
        role = payload.get("role")

        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        doctor_id = doctor_name = None
        patient_name = None

        if role.lower() == "doctor":
            doctor = db.query(models.Doctor).filter(models.Doctor.user_id == user_id).first()
            if doctor:
                doctor_id = doctor.id
                doctor_name = doctor.name

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

    except HTTPException:
        raise

    except Exception as e:
        print("Token validation error:", str(e))
        raise HTTPException(status_code=500, detail="Token validation failed")