from pydantic import BaseSettings, SecretStr
from pydantic.env_settings import SettingsSourceCallable
from typing import Tuple

class POAPSettings(BaseSettings):
    url: str

    class Config:
        env_prefix = 'poap_'

        @classmethod
        def customise_sources(
                cls,
                init_settings: SettingsSourceCallable,
                env_settings: SettingsSourceCallable,
                file_secret_settings: SettingsSourceCallable,
            ) -> Tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings
            