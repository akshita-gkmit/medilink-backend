from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.db.database import get_db
from app.schemas import schemas 
from app.models import models

router = APIRouter(prefix="/patient", tags=["Patient"])

# 1. Returns list of active doctors with basic details.
@router.get("/doctors")
def get_all_doctors(db: Session = Depends(get_db)):

    doctors = db.query(models.Doctor).filter(
        models.Doctor.deleted_at.is_(None)
    ).all()

    return [
        {
            "id": d.id,
            "name": d.name,
            "specialization": d.specialization,
            "qualification": d.qualification,
        }
        for d in doctors
    ]

# 2. Returns all non-cancelled appointments for a patient.
@router.get("/appointments/{patient_id}")
def get_patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    
    appts = (
        db.query(models.Appointment)
        .join(models.Slot)
        .join(models.Doctor)
        .filter(models.Appointment.patient_id == patient_id)
        .filter(models.Appointment.status != "Cancelled") 
        .all()
    )

    return [
        {
            "id": a.id,
            "doctor_name": a.doctor.name,
            "date": a.slot.date,
            "start_time": a.slot.start_time.strftime("%H:%M"),
            "end_time": a.slot.end_time.strftime("%H:%M"),
            "status": a.status
        }
        for a in appts
    ]

# 3. Allows patient to book a slot if it's available.
@router.post("/appointment/book")
def book_appointment(data: schemas.BookAppointment, db: Session = Depends(get_db)):
    slot = db.query(models.Slot).filter(
        models.Slot.id == data.slot_id,
        models.Slot.status == "Available",
        models.Slot.deleted_at.is_(None)
    ).first()

    if not slot:
        raise HTTPException(400, "Slot not available")

    appointment = models.Appointment(
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        slot_id=data.slot_id,
    )

    slot.status = "Booked"
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return {"message": "Appointment booked", "appointment_id": appointment.id}

# 4. Returns patient_id mapped to the logged-in user's user_id.
@router.get("/by-user/{user_id}")
def get_patient_by_user(user_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(
        models.Patient.user_id == user_id
    ).first()

    if not patient:
        raise HTTPException(404, "Patient not found")

    return {"patient_id": patient.id}

# 5. Marks appointment as cancelled and frees the slot.
@router.delete("/cancel/{appointment_id}")
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()

    if not appt:
        raise HTTPException(404, "Appointment not found")

    # mark slot free again
    slot = db.query(models.Slot).filter(models.Slot.id == appt.slot_id).first()

    if slot:
        slot.status = "Available"

    # DO NOT DELETE — just update status
    appt.status = "Cancelled"
    appt.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "Appointment cancelled successfully"}

# 6. Returns all past & current appointments of a patient.
@router.get("/appointments/history/{patient_id}")
def get_history(patient_id: int, db: Session = Depends(get_db)):

    appts = (
        db.query(models.Appointment)
        .join(models.Slot)
        .join(models.Doctor)
        .filter(models.Appointment.patient_id == patient_id)
        .all()  # INCLUDE everything
    )

    return [
        {
            "id": a.id,
            "doctor_name": a.doctor.name,
            "date": a.slot.date,
            "start_time": a.slot.start_time.strftime("%H:%M"),
            "end_time": a.slot.end_time.strftime("%H:%M"),
            "status": a.status
        }
        for a in appts
    ]

# 7. Returns available slots of a doctor, optionally filtered by date.
@router.get("/doctor/{doctor_id}/slots")
def get_doctor_slots_for_patient(
    doctor_id: int,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    doctor = db.query(models.Doctor).filter(
        models.Doctor.id == doctor_id,
        models.Doctor.deleted_at.is_(None)
    ).first()

    if not doctor:
        raise HTTPException(404, "Doctor not found")

    query = db.query(models.Slot).filter(
        models.Slot.doctor_id == doctor_id,
        models.Slot.status == "Available",
        models.Slot.deleted_at.is_(None)
    )

    if date:
        query = query.filter(models.Slot.date == date)

    slots = query.order_by(models.Slot.start_time).all()

    return [
        {
            "slot_id": s.id,
            "date": s.date,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "status": s.status
        }
        for s in slots
    ]