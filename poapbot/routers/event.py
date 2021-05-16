from poapbot.db.exceptions import ConflictError, DoesNotExist
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional

from poapbot.db import POAPDatabase
from poapbot.db.models import Event, EventCreate, EventUpdate

from ..dependencies import get_db

router = APIRouter(
    prefix="/events",
    tags=["events"],
    dependencies=[Depends(get_db)]
)

@router.post("/", description="Create Event", response_model=Event)
async def create_event(event: EventCreate, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.create_event(event)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/{id}", response_model=Event)
async def get_event_by_id(id: str, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.get_event_by_id(id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{id}", response_model=Event)
async def update_event(event: EventUpdate, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.update_event(event)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{id}", response_model=Event)
async def delete_event(id: str, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.delete_event_by_id(id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
