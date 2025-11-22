from datetime import datetime, timedelta, time, date
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import models
from app.schemas.slot_schema import SlotCreate
from app.config.auth import RoleChecker
from app.config.auth import verify_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


# bearer_scheme = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/doctor", tags=["Doctor Slots"])
doctor_access = RoleChecker(["doctor"])


# 1️ Doctor Dashboard
@router.get("/dashboard/{doctor_id}")
def doctor_dashboard(doctor_id: int, db: Session = Depends(get_db)):
    today = date.today()

    # Check doctor existence
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    try:
        today_appts = db.query(models.Appointment).join(models.Slot).filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.status == "approved",
            models.Slot.date == today
        ).count()

        total_patients = db.query(models.Appointment.patient_id).filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.status == "approved"
        ).distinct().count()

        upcoming = db.query(models.Appointment).join(models.Slot).filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.status == "approved",
            models.Slot.date > today
        ).count()

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")

    return {
        "todayAppointments": today_appts,
        "totalPatients": total_patients,
        "upcomingAppointments": upcoming,
    }


# 2 Fetch slots for a doctor
@router.get("/slots")
def get_slots(doctor_id: int, date: date, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    slots = db.query(models.Slot).filter(
        models.Slot.doctor_id == doctor_id,
        models.Slot.date == date
    ).all()

    if not slots:
        raise HTTPException(status_code=404, detail="No slots found for this date")

    return {"doctor_id": doctor_id, "date": date, "slots": slots}


# 3 Create Slots (doctor only)
@router.post("/slots/create", dependencies=[Depends(doctor_access)])
def create_doctor_slots(payload: SlotCreate, db: Session = Depends(get_db)):
    today = date.today()
    now = datetime.now().time()
    max_date = today + timedelta(days=7)

    # Validate doctor
    doctor = db.query(models.Doctor).filter(models.Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Validate date range
    if payload.date < today:
        raise HTTPException(status_code=400, detail="You cannot create slots for a past date")

    if payload.date > max_date:
        raise HTTPException(status_code=400, detail="You can only create slots within 7 days from today")

    if not payload.slots or len(payload.slots) == 0:
        raise HTTPException(status_code=400, detail="No time slots provided")

    if payload.date == today:
    for slot in payload.slots:
        slot_start = datetime.strptime(slot.start_time, "%H:%M").time()
        slot_end = datetime.strptime(slot.end_time, "%H:%M").time()

        if slot_start < now:
            raise HTTPException(
                status_code=400,
                detail="Cannot create slot earlier than the current time"
            )

    # Remove existing slots
    try:
        db.query(models.Slot).filter(
            models.Slot.doctor_id == payload.doctor_id,
            models.Slot.date == payload.date
        ).delete()
        db.commit()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete previous slots")

    # Create new slots
    try:
        for t in payload.slots:
            try:
                start = datetime.strptime(t, "%H:%M").time()
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid time format: {t}. Use HH:MM")

            end = (datetime.combine(payload.date, start) + timedelta(minutes=30)).time()

            # Prevent creating past slots
            if payload.date == today and start <= now:
                raise HTTPException(
                    status_code=400,
                    detail=f"Slot time {t} is already past. Cannot create past slots."
                )

            slot = models.Slot(
                doctor_id=payload.doctor_id,
                date=payload.date,
                start_time=start,
                end_time=end,
                status="Available"
            )
            db.add(slot)

        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save slots")

    return {"message": "Slots saved successfully"}


# 4 Validate slot date (used internally)
def validate_slot_date(selected_date: date):
    today = date.today()
    max_date = today + timedelta(days=7)

    if selected_date < today:
        raise HTTPException(status_code=400, detail="Date cannot be in the past")

    if selected_date > max_date:
        raise HTTPException(
            status_code=400,
            detail="Date can only be within 7 days from today"
        )


# 5 Admin fetches full doctor profile
@router.get("/{doctor_id}", dependencies=[Depends(RoleChecker(["admin"]))])
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = (
        db.query(models.Doctor, models.User)
        .join(models.User, models.Doctor.user_id == models.User.id)
        .filter(models.Doctor.id == doctor_id)
        .first()
    )

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor_data, user_data = doctor

    return {
        "id": doctor_data.id,
        "name": doctor_data.name,
        "email": user_data.email,
        "specialization": doctor_data.specialization,
        "qualification": doctor_data.qualification,
        "position": doctor_data.position,
        "dob": doctor_data.dob.isoformat() if doctor_data.dob else None,
        "chamber": doctor_data.chamber,
        "start_time": doctor_data.start_time.isoformat() if doctor_data.start_time else None,
        "end_time": doctor_data.end_time.isoformat() if doctor_data.end_time else None,
        "consultation_fee": doctor_data.consultation_fee,
        "created_at": doctor_data.created_at.isoformat() if doctor_data.created_at else None,
        "updated_at": doctor_data.updated_at.isoformat() if doctor_data.updated_at else None,
        "deleted_at": doctor_data.deleted_at.isoformat() if doctor_data.deleted_at else None,
    }



# 6 Get doctor appointments
@router.get("/{doctor_id}/appointments")
def get_doctor_appointments(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    appointments = db.query(models.Appointment).join(models.Slot).join(models.Patient).filter(
        models.Appointment.doctor_id == doctor_id
    ).order_by(models.Slot.date.desc()).all()

    if not appointments:
        raise HTTPException(status_code=404, detail="No appointments found")

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
