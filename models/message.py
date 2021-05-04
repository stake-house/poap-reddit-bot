import ormar
from datetime import datetime
from typing import List, Optional

from . import BaseMeta

class RequestMessage(ormar.Model):

    class Meta(BaseMeta):
        tablename = "request_messages"

    id: int = ormar.String(primary_key=True, max_length=100)
    author: str = ormar.String(max_length=100)
    created: datetime = ormar.DateTime()
    subject: str = ormar.String(max_length=1024)
    body: str = ormar.String(max_length=1024)