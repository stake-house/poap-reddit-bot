from pydantic import BaseSettings
from pydantic.env_settings import SettingsSourceCallable
from typing import Tuple

class DBSettings(BaseSettings):
    url: str

    class Config:
        env_prefix = 'db_'

        @classmethod
        def customise_sources(
                cls,
                init_settings: SettingsSourceCallable,
                env_settings: SettingsSourceCallable,
                file_secret_settings: SettingsSourceCallable,
            ) -> Tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings
            