import ormar
from pydantic import BaseModel
from datetime import datetime

from . import BaseMeta

class Event(ormar.Model):
    class Meta(BaseMeta):
        tablename = "events"
        constraints = [ormar.UniqueColumns('code')]

    id: str = ormar.String(primary_key=True, max_length=100)
    name: str = ormar.String(max_length=256)
    description: str = ormar.String(max_length=256)
    code: str = ormar.String(max_length=256)
    expiry_date: datetime = ormar.DateTime()

    def expired(self):
        return self.expiry_date < datetime.utcnow()