import ormar
import sqlalchemy
import databases
from datetime import datetime

import yaml
from .settings import DBSettings

SETTINGS = yaml.safe_load(open('settings.yaml', 'r'))
DB_SETTINGS = DBSettings.parse_obj(SETTINGS['db'])

metadata = sqlalchemy.MetaData()
database = databases.Database(DB_SETTINGS.url)

class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database

from .event import Event
from .attendee import Attendee
from .admin import Admin
from .claim import Claim
from .message import RequestMessage, ResponseMessage