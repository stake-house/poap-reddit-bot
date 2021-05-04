from pydantic import BaseSettings, SecretStr

class AuthSettings(BaseSettings):
    username: str
    password: SecretStr
    client_id: str
    client_secret: SecretStr
    user_agent: str

    class Config:
        env_prefix = 'reddit_auth_'

class RedditSettings(BaseSettings):
    auth: AuthSettings