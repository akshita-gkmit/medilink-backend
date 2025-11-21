from datetime import datetime, date, time, timedelta

def validate_slot_datetime(slot_date: date, slot_start: time):
    now = datetime.utcnow()
    cutoff = now + timedelta(hours=1)

    slot_dt = datetime.combine(slot_date, slot_start)

    if slot_dt.date() < now.date():
        return False

    if slot_dt < cutoff:
        return False
    
    return True