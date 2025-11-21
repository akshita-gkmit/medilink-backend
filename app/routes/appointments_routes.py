from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, time as dt_time, date as dt_date, date
from app.config.auth import RoleChecker
from app.db.database import get_db
from app.models.models import Appointment, Slot
from app.schemas.schemas import AppointmentCreate, AppointmentCancel
from app.models.models import Slot  # adjust import if your models file path differs
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/appointments", tags=["Appointments"])
patient_access=RoleChecker(["patient"])

# 1. Allows a patient to book an available slot after validations.
@router.post("/book", dependencies=[Depends(patient_access)])
def book_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):

    slot = db.query(Slot).filter(Slot.id == data.slot_id).first()
    if not slot:
        raise HTTPException(404, "Slot not found.")

    if slot.doctor_id != data.doctor_id:
        raise HTTPException(400, "Slot does not belong to this doctor.")

    if slot.status != "Available":
        raise HTTPException(400, "Slot is not available for booking.")

    # Prevent double-booking (extra safety)
    existing = db.query(Appointment).filter(
        Appointment.slot_id == data.slot_id
    ).first()

    if existing:
        raise HTTPException(400, "Slot already booked.")

    # Create appointment
    appointment = Appointment(
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        slot_id=data.slot_id,
        reason_for_visit=data.reason_for_visit,
        booked_at=date.today(),
        status="Pending"
    )
    db.add(appointment)
    slot.status = "Pending"
    db.commit()
    db.refresh(appointment)
    return {
        "message": "Appointment request submitted.",
        "appointment_id": appointment.id,
        "status": appointment.status
    }

# 2. Allows a patient to cancel their appointment and free the slot.
@router.post("/cancel", dependencies=[Depends(patient_access)])
def cancel_appointment(data: AppointmentCancel, db: Session = Depends(get_db)):

    appointment = db.query(Appointment).filter(
        Appointment.id == data.appointment_id,
        Appointment.patient_id == data.patient_id
    ).first()

    if not appointment:
        raise HTTPException(404, "Appointment not found.")

    if appointment.status in ["Cancelled", "Rejected", "Completed"]:
        raise HTTPException(400, "Appointment cannot be cancelled.")

    slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()

    appointment.status = "Cancelled"
    slot.status = "Available"
    db.commit()
    return {"message": "Appointment cancelled successfully."}

# 3. Allows a doctor to approve a patient’s appointment request.
@router.patch("/{appointment_id}/approve", dependencies=[Depends(RoleChecker(["doctor"]))])
def approve_appointment(appointment_id: int, db: Session = Depends(get_db)):

    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = "approved"
    db.commit()
    return {"message": "Appointment approved Successfully"}

# 4. Allows a doctor to reject a patient’s appointment request.
@router.patch("/{appointment_id}/reject", dependencies=[Depends(RoleChecker(["doctor"]))])
def reject_appointment(appointment_id: int, db: Session = Depends(get_db)):

    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = "rejected"
    db.commit()
    return {"message": "Appointment rejected Successfully"}



router = APIRouter(prefix="/doctor", tags=["doctor"])

class SlotOut(BaseModel):
    id: int
    doctor_id: int
    date: str
    start_time: str
    end_time: str
    status: str

    class Config:
        orm_mode = True


@router.get("/{doctor_id}/slots", response_model=List[SlotOut])
def get_available_slots(
    doctor_id: int,
    date: dt_date = Query(..., description="Date in YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Return slots for `doctor_id` on a given date that start at least 1 hour
    after current time (server time).
    """
    # Validate input date
    if not isinstance(date, dt_date):
        raise HTTPException(status_code=422, detail="Invalid date")

    # Query DB for available slots (status = 'Available')
    try:
        slots_q = (
            db.query(Slot)
            .filter(Slot.doctor_id == doctor_id)
            .filter(Slot.date == date)
            .filter(Slot.status == "Available")
            .all()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    now = datetime.utcnow()
    cutoff = now + timedelta(hours=1)

    result = []
    for s in slots_q:
        try:
            slot_dt = datetime.combine(s.date, s.start_time)
        except Exception:
            continue
        if slot_dt >= cutoff:
            result.append(s)

    return result