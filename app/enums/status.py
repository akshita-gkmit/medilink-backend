class SlotStatus(str, Enum):
    AVAILABLE = "Available"
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    INACTIVE = "Inactive"
    REJECTED = "Rejected"
    BUSY = "Busy"
