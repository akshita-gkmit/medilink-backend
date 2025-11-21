from pydantic import BaseModel
from datetime import date, time
from typing import Optional, List

class SlotCreate(BaseModel):
    doctor_id: int
    date: date
    slots: List[str]