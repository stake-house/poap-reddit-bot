import ormar
from datetime import datetime
from typing import List, Optional

from . import BaseMeta
from .event import Event

class Attendee(ormar.Model):
    
    class Meta(BaseMeta):
        tablename = "attendees"

    id: str = ormar.String(primary_key=True, max_length=100)
    attended_events: Optional[List[Event]] = ormar.ManyToMany(Event)