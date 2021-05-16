from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional
from poapbot.db import POAPDatabase, ConflictError
from poapbot.db.models import Admin, AdminCreate

from ..dependencies import get_db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_db)]
)

@router.post(
    "/create_admin",
    description="Create Admin",
    tags=['admin'],
    response_model=Admin
)
async def create_admin(admin: AdminCreate, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.create_admin(admin)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
