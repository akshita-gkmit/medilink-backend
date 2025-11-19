from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.config.auth import RoleChecker
from app.db.database import get_db
from app.models.models import Appointment, Slot
from app.schemas.schemas import AppointmentCreate, AppointmentCancel

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