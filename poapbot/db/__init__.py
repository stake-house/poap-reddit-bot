from databases import Database
import sqlalchemy
import yaml

from poapbot.settings import DBSettings
SETTINGS = yaml.safe_load(open('settings.yaml', 'r'))
DB_SETTINGS = DBSettings.parse_obj(SETTINGS['db'])

metadata = sqlalchemy.MetaData()
database = Database(DB_SETTINGS.url)

from .database import POAPDatabase
from .exceptions import *