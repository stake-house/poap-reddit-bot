import ormar
from datetime import datetime
from typing import List, Optional

from . import BaseMeta
from .event import Event
from .participant import Participant
from .message import RequestMessage

class Claim(ormar.Model):

    class Meta(BaseMeta):
        tablename = "claims"
        constraints = [ormar.UniqueColumns('participant','event')]

    id: int = ormar.Integer(primary_key=True)
    participant: Participant = ormar.ForeignKey(Participant)
    event: Event = ormar.ForeignKey(Event)
    link: str = ormar.String(max_length=256)
    notified: Optional[bool] = ormar.Boolean(default=False)