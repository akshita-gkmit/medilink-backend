from datetime import datetime, timedelta, time, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import models
from app.schemas.doctor_schema import DoctorAdminCreate, DoctorAdminUpdate, DoctorAdminResponse, DoctorPublicResponse
from app.config.auth import get_current_user
from app.config.auth import RoleChecker
from app.schemas.slot_schema import SlotCreate

router = APIRouter(prefix="/doctor", tags=["Doctor Slots"])
doctor_access=RoleChecker(["doctor"])

# 1.Returns today's, total, and upcoming approved appointments for a doctor.
@router.get("/dashboard/{doctor_id}")
def doctor_dashboard(doctor_id: int, db: Session = Depends(get_db)):
    today = date.today()

    # APPROVED & TODAY appointments
    today_appointments = db.query(models.Appointment).join(
        models.Slot
    ).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.status == "approved",
        models.Slot.date == today
    ).count()

    # Total unique patients (only approved)
    total_patients = db.query(models.Appointment.patient_id).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.status == "approved"
    ).distinct().count()

    # Upcoming only approved
    upcoming_appointments = db.query(models.Appointment).join(
        models.Slot
    ).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.status == "approved",
        models.Slot.date > today
    ).count()

    return {
        "todayAppointments": today_appointments,
        "totalPatients": total_patients,
        "upcomingAppointments": upcoming_appointments,
    }

# 2. Returns all slots of a doctor for a given date.
@router.get("/slots")
def get_slots(doctor_id: int, date: date, db: Session = Depends(get_db)):
    slots = db.query(models.Slot).filter(
        models.Slot.doctor_id == doctor_id,
        models.Slot.date == date
    ).all()

    return {"doctor_id": doctor_id, "date": date, "slots": slots}

# 3. Doctor adds new 30-minute slots (replaces old slots for same date).
@router.post("/slots/create", dependencies=[Depends(doctor_access)])
def create_doctor_slots(payload: SlotCreate, db: Session = Depends(get_db)):

    # Remove old slots for same doctor + date
    db.query(models.Slot).filter(
        models.Slot.doctor_id == payload.doctor_id,
        models.Slot.date == payload.date
    ).delete()
    db.commit()

    # Insert new slots
    for t in payload.slots:
        start = datetime.strptime(t, "%H:%M").time()
        end_dt = datetime.strptime(t, "%H:%M") + timedelta(minutes=30)

        slot = models.Slot(
            doctor_id=payload.doctor_id,
            date=payload.date,
            start_time=start,
            end_time=end_dt.time(),
            status="Available"
        )
        db.add(slot)

    db.commit()
    return {"message": "Slots saved successfully"}

# 4. Ensures selected date is not past and not beyond 7 days ahead.
def validate_slot_date(selected_date: date):
    today = date.today()
    max_date = today + timedelta(days=7)

    if selected_date < today:
        raise HTTPException(
            status_code=400,
            detail="Date cannot be in the past."
        )

    if selected_date > max_date:
        raise HTTPException(
            status_code=400,
            detail="Date can only be within 7 days from today."
        )
    
# 5. Admin fetches complete doctor profile with timings and personal info.
@router.get("/{doctor_id}", dependencies=[Depends(RoleChecker(["admin"]))])
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")

    user = db.query(models.User).filter(models.User.id == doctor.user_id).first()

    return {
        "id": doctor.id,
        "name": doctor.name,
        "email": user.email,
        "specialization": doctor.specialization,
        "qualification": doctor.qualification,
        "position": doctor.position,
        "dob": doctor.dob.isoformat() if doctor.dob else None,
        "chamber": doctor.chamber,
        "start_time": str(doctor.start_time) if doctor.start_time else None,
        "end_time": str(doctor.end_time) if doctor.end_time else None,
        "consultation_fee": doctor.consultation_fee,
        "created_at": doctor.created_at.isoformat() if doctor.created_at else None,
        "updated_at": doctor.updated_at.isoformat() if doctor.updated_at else None,
        "deleted_at": doctor.deleted_at.isoformat() if doctor.deleted_at else None,
    }

# 6. Returns all appointments of a doctor with slot timing and status.
@router.get("/{doctor_id}/appointments")
def get_doctor_appointments(doctor_id: int, db: Session = Depends(get_db)):
    appointments = (
        db.query(models.Appointment)
        .join(models.Slot, models.Appointment.slot_id == models.Slot.id)
        .join(models.Patient, models.Appointment.patient_id == models.Patient.id)
        .filter(models.Appointment.doctor_id == doctor_id)
        .order_by(models.Slot.date.desc())
        .all()
    )

    return [
        {
            "id": appt.id,
            "patient_name": appt.patient.name,
            "date": appt.slot.date,
            "start_time": appt.slot.start_time.strftime("%H:%M"),
            "end_time": appt.slot.end_time.strftime("%H:%M"),
            "status": appt.status,
        }
        for appt in appointments
    ]
