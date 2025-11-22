import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from app.models import models
from app.schemas import schemas
from app.db.database import get_db
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
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
    

@router.post("/forgot-password")
def forgot_password(request: schemas.ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):

    # 1. Find user
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    # 2. Generate token + expiration
    reset_token = generate_reset_token()
    expiry_time = datetime.utcnow() + timedelta(minutes=30)

    user.reset_token = reset_token
    user.reset_token_expires = expiry_time
    db.commit()

    # 3. Send email
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"

    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_PORT=int(os.getenv("MAIL_PORT")),
        MAIL_SERVER=os.getenv("MAIL_SERVER"),
        MAIL_FROM=os.getenv("MAIL_FROM"),
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        VALIDATE_CERTS=True
    )

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[request.email],
        body=f"""
            <h3>Password Reset</h3>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_link}">{reset_link}</a>
            <p>This link expires in 30 minutes.</p>
        """,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

    return {"message": "Reset link sent to your email"}

def generate_reset_token():
    return str(uuid.uuid4())

@router.post("/reset-password")
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.reset_token == request.token).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid token")
    if user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired")
    user.password_hash = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expires = None

    db.commit()
    return {"message": "Password reset successful"}