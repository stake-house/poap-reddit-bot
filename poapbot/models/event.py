import ormar
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from . import BaseMeta

class Event(ormar.Model):
    class Meta(BaseMeta):
        tablename = "events"
        constraints = [ormar.UniqueColumns('code')]

    id: str = ormar.String(primary_key=True, max_length=100)
    name: str = ormar.String(max_length=256)
    description: Optional[str] = ormar.String(max_length=256, default="")
    code: str = ormar.String(max_length=256)
    start_date: datetime = ormar.DateTime()
    expiry_date: datetime = ormar.DateTime()

    minimum_karma: int = ormar.Integer(default=0)
    minimum_age: int = ormar.Integer(default=0)

    def expired(self):
        return self.expiry_date < datetime.utcnow()

    def started(self):
        return self.start_date < datetime.utcnow()