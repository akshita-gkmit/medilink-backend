from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import models
from app.schemas import schemas
from app.db.database import get_db
from app.config.auth import get_password_hash, verify_password, create_access_token, create_refresh_token
from datetime import datetime

router = APIRouter(prefix="", tags=["Authentication"])


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


@router.post("/login", response_model=schemas.TokenResponse)
def login_user(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter(models.User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_role = (
        db.query(models.Role.name)
        .join(models.UserRole, models.UserRole.role_id == models.Role.id)
        .filter(models.UserRole.user_id == user.id)
        .first()
    )

    if not user_role:
        raise HTTPException(status_code=400, detail="Role not assigned")

    role_name = user_role[0]   #patient / doctor / admin


    token_data = {"sub": user.email, "role": role_name}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": role_name
    }
