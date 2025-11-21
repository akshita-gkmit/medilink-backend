from sqlalchemy.orm import Session
from app.models import User, Role, UserRole, Doctor, Patient
from passlib.context import CryptContext
import logging
from app.enums.gender import GenderEnum

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLES = ["admin", "doctor", "patient"]

ADMIN_EMAIL = "admin@medilink.com"
DOCTOR_EMAIL = "doctor1@medilink.com"
PATIENT_EMAIL = "patient1@gmail.com"

DEFAULT_PASSWORD = "Password@123"

def _seed_roles(db: Session):
    existing_roles = {r.name for r in db.query(Role).all()}

    required_roles = {"Admin", "Doctor", "Patient"}

    missing_roles = required_roles - existing_roles

    if missing_roles:
        for role_name in missing_roles:
            db.add(Role(name=role_name))
        db.commit()
        logger.info(f"Added missing roles: {', '.join(missing_roles)}")
    else:
        logger.info("All roles already exist.")

def _create_user(db: Session, email: str, role_name: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        logger.info(f"{role_name} user already exists.")
        return user

    hashed_password = pwd_context.hash(DEFAULT_PASSWORD)

    user = User(email=email, password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    role = db.query(Role).filter(Role.name == role_name).first()
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db.add(user_role)
    db.commit()

    logger.info(f"{role_name} user created.")
    return user

def _seed_admin(db: Session):
    return _create_user(db, ADMIN_EMAIL, "Admin")

def _seed_doctor(db: Session):
    user = _create_user(db, DOCTOR_EMAIL, "Doctor")

    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if doctor:
        logger.info("Doctor record already exists.")
        return

    doctor = Doctor(
        user_id=user.id,
        name="Dr. John Doe",
        specialization="General Physician",
        qualification="MBBS",
        position="Senior Consultant",
        chamber="Room 101",
        consultation_fee=500
    )
    db.add(doctor)
    db.commit()
    logger.info("Doctor details seeded.")

def _seed_patient(db: Session):
    user = _create_user(db, PATIENT_EMAIL, "Patient")

    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if patient:
        logger.info("Patient record already exists.")
        return

    patient = Patient(
        user_id=user.id,
        name="Jane Smith",
        gender=GenderEnum.female ,
    )
    db.add(patient)
    db.commit()
    logger.info("Patient details seeded.")


def run_seeder(db: Session):
    logger.info("---- Running Seeder ----")
    _seed_roles(db)
    _seed_admin(db)
    _seed_doctor(db)
    _seed_patient(db)
    logger.info("---- Seeding Complete ----")
