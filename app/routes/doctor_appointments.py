from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.config.auth import RoleChecker
from app.db.database import get_db
from app.models.models import Appointment, Slot
from app.schemas.schemas import AppointmentStatusUpdate

router = APIRouter(prefix="/doctor/appointments", tags=["Doctor Appointments"])
doctor_access=RoleChecker(["doctor"])

# 1. Allows a doctor to approve or reject an appointment with optional notes.
@router.post("/update-status", dependencies=[Depends(doctor_access)])
def update_appointment_status(data: AppointmentStatusUpdate, db: Session = Depends(get_db)):

    appointment = db.query(Appointment).filter(
        Appointment.id == data.appointment_id
    ).first()

    if not appointment:
        raise HTTPException(404, "Appointment not found.")

    slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()
    # APPROVE → Confirm appointment
    if data.action.lower() == "approve":
        appointment.status = "Approved"
        slot.status = "Confirmed"
        appointment.notes = data.notes
        db.commit()
        return {"message": "Appointment approved successfully."}
    # REJECT → Free the slot
    elif data.action.lower() == "reject":
        appointment.status = "Rejected"
        slot.status = "Inactive" 
        appointment.notes = data.notes
        db.commit()
        return {"message": "Appointment rejected successfully."}
    # Invalid action
    else:
        raise HTTPException(400, "Invalid action. Use 'approve' or 'reject'.")

# 2. Returns a doctor's appointments with patient name and slot timings.
@router.get("/doctor/{doctor_id}/appointments")
def get_doctor_appointments(doctor_id: int, db: Session = Depends(get_db)):
    appointments = (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor_id)
        .order_by(Appointment.date)
        .all()
    )

    result = []
    for a in appointments:
        result.append({
            "id": a.id,
            "patient_name": a.patient.name if a.patient else None,
            "date": str(a.date),
            "start_time": str(a.start_time),
            "end_time": str(a.end_time),
            "status": a.status
        })

    return result

# 3. Marks a specific appointment as approved.
@router.patch("/doctor/appointments/{appointment_id}/approve")
def approve_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter_by(id=appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = "approved"
    db.commit()

    return {"message": "Appointment approved"}

# 4. Marks a specific appointment as rejected.
@router.patch("/doctor/appointments/{appointment_id}/reject")
def reject_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter_by(id=appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = "rejected"
    db.commit()

    return {"message": "Appointment rejected"}