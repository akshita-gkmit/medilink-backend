from sqlalchemy.orm import Session
from app.models import User, Role, UserRole, Doctor, Patient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---- DEFAULT SEED DATA ----
ROLES = ["Admin", "Doctor", "Patient"]

ADMIN_EMAIL = "admin@medilink.com"
DOCTOR_EMAIL = "doctor1@medilink.com"
PATIENT_EMAIL = "patient1@gmail.com"

DEFAULT_PASSWORD = "Password@123"


def seed_roles(db: Session):
    """Seed default roles if missing."""
    existing_roles = {r.name for r in db.query(Role).all()}

    required_roles = {"Admin", "Doctor", "Patient"}

    missing_roles = required_roles - existing_roles

    if missing_roles:
        for role_name in missing_roles:
            db.add(Role(name=role_name))
        db.commit()
        print(f"Added missing roles: {', '.join(missing_roles)}")
    else:
        print("All roles already exist.")



def create_user(db: Session, email: str, role_name: str):
    """Create a user with the given role if not exists."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"{role_name} user already exists.")
        return user

    hashed_password = pwd_context.hash(DEFAULT_PASSWORD)

    user = User(email=email, password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Attach role
    role = db.query(Role).filter(Role.name == role_name).first()
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db.add(user_role)
    db.commit()

    print(f"{role_name} user created.")
    return user


def seed_admin(db: Session):
    return create_user(db, ADMIN_EMAIL, "Admin")


def seed_doctor(db: Session):
    user = create_user(db, DOCTOR_EMAIL, "Doctor")

    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if doctor:
        print("Doctor record already exists.")
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
    print("Doctor details seeded.")


def seed_patient(db: Session):
    user = create_user(db, PATIENT_EMAIL, "Patient")

    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if patient:
        print("Patient record already exists.")
        return

    patient = Patient(
        user_id=user.id,
        name="Jane Smith",
        gender="Female",
    )
    db.add(patient)
    db.commit()
    print("Patient details seeded.")


def run_seeder(db: Session):
    print("---- Running Seeder ----")
    seed_roles(db)
    seed_admin(db)
    seed_doctor(db)
    seed_patient(db)
    print("---- Seeding Complete ----")
