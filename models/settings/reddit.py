from pydantic import BaseModel, SecretStr

class AuthSettings(BaseModel):
    username: str
    password: SecretStr
    client_id: str
    client_secret: SecretStr
    user_agent: str

    class Config:
        env_prefix = 'reddit_auth_'

class RedditSettings(BaseModel):
    auth: AuthSettings