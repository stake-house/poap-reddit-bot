import sqlalchemy

from poapbot.db import metadata, DB_SETTINGS

engine = sqlalchemy.create_engine(DB_SETTINGS.url)
metadata.create_all(engine)