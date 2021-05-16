from pydantic import BaseSettings
from typing import List, Dict

class FastAPISettings(BaseSettings):
    title: str
    version: str
    openapi_tags: List[Dict[str, str]]

    class Config:
        env_prefix = 'fastapi_'
