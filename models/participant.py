import ormar
from datetime import datetime
from typing import List, Optional

from . import BaseMeta
from .event import Event

class Participant(ormar.Model):
    
    class Meta(BaseMeta):
        tablename = "participants"

    id: str = ormar.String(primary_key=True, max_length=100)
    attended_events: Optional[List[Event]] = ormar.ManyToMany(Event)