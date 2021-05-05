from pydantic import BaseSettings

class DBSettings(BaseSettings):
    url: str

    class Config:
        env_prefix = 'db_'