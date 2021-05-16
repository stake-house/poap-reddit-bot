from pydantic import BaseModel
import ormar
from datetime import datetime
from typing import List, Optional

from . import BaseMeta

class Attendee(ormar.Model):
    
    class Meta(BaseMeta):
        tablename = "attendees"
        constraints = [ormar.UniqueColumns('username')]

    id: str = ormar.Integer(primary_key=True)
    username: str = ormar.String(max_length=100)

class AttendeeCreate(BaseModel):

    username: str
