from app.enums.status import status

class SlotStatus(str, status):
    AVAILABLE = "Available"
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    INACTIVE = "Inactive"
    REJECTED = "Rejected"
    BUSY = "Busy"
