import ormar
from datetime import datetime
from typing import List, Optional

from . import BaseMeta
from .claim import Claim

class RequestMessage(ormar.Model):

    class Meta(BaseMeta):
        tablename = "request_messages"

    id: int = ormar.Integer(primary_key=True)
    secondary_id: str = ormar.String(max_length=100)
    username: str = ormar.String(max_length=100)
    created: datetime = ormar.DateTime()
    subject: str = ormar.String(max_length=1024, nullable=True)
    body: str = ormar.String(max_length=1024)

class ResponseMessage(ormar.Model):

    class Meta(BaseMeta):
        tablename = "response_messages"

    id: int = ormar.Integer(primary_key=True)
    secondary_id: str = ormar.String(max_length=100)
    username: str = ormar.String(max_length=100)
    created: datetime = ormar.DateTime()
    body: str = ormar.String(max_length=1024)