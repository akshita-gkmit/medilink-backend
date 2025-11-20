from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.auth import RoleChecker, verify_token
from typing import Optional
from app.db.database import get_db
from app.config.auth import get_password_hash
from app.models import models
from app.schemas.doctor_schema import DoctorAdminCreate, DoctorAdminUpdate
from datetime import datetime

router = APIRouter(prefix="/doctors", tags=["Doctors"])


