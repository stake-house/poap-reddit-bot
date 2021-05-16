from ormar import ModelMeta

from poapbot.db import metadata, database

class BaseMeta(ModelMeta):
    metadata = metadata
    database = database

from .event import Event, EventCreate, EventUpdate
from .attendee import Attendee, AttendeeCreate
from .admin import Admin, AdminCreate
from .claim import Claim, ClaimCreate
from .message import RequestMessage, RequestMessageCreate, ResponseMessage, ResponseMessageCreate

__all__ = [
    'Event',
    'EventCreate',
    'EventUpdate',
    'Attendee',
    'AttendeeCreate',
    'Admin',
    'AdminCreate',
    'Claim',
    'ClaimCreate',
    'RequestMessage',
    'RequestMessageCreate',
    'ResponseMessage',
    'ResponseMessageCreate'
]