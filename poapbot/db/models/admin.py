from pydantic import BaseModel
import ormar
from datetime import datetime
from typing import List, Optional

from . import BaseMeta

class Admin(ormar.Model):
    
    class Meta(BaseMeta):
        tablename = "admins"
        constraints = [ormar.UniqueColumns('username')]

    id: int = ormar.Integer(primary_key=True)
    username: str = ormar.String(max_length=100)

class AdminCreate(BaseModel):

    username: str