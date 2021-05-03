from pydantic import BaseModel, Field
from uuid import uuid4 as uuid
from datetime import datetime
from enum import Enum

class AttendanceType(Enum):
    STATIC = "STATIC" # fixed attendance list
    DYNAMIC = "DYNAMIC" # will look for new attendance until expiry

class Event(BaseModel):
    _id: str = Field(default_factory=lambda: str(uuid()))
    name: str
    description: str = ""
    attendance_type = AttendanceType
    expiry_date: datetime