from pydantic import BaseSettings, SecretStr
from pydantic.env_settings import SettingsSourceCallable
from typing import Tuple

class AuthSettings(BaseSettings):
    username: str
    password: SecretStr
    client_id: str
    client_secret: SecretStr
    user_agent: str

    class Config:
        env_prefix = 'reddit_auth_'

        @classmethod
        def customise_sources(
                cls,
                init_settings: SettingsSourceCallable,
                env_settings: SettingsSourceCallable,
                file_secret_settings: SettingsSourceCallable,
            ) -> Tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings

class RedditSettings(BaseSettings):
    auth: AuthSettings
    