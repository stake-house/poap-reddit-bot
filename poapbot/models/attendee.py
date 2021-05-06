import ormar
from datetime import datetime
from typing import List, Optional

from . import BaseMeta
from .event import Event

class Attendee(ormar.Model):
    
    class Meta(BaseMeta):
        tablename = "attendees"
        constraints = [ormar.UniqueColumns('username')]

    id: str = ormar.Integer(primary_key=True)
    username: str = ormar.String(max_length=100)