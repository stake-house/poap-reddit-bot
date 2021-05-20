from poapbot.db.models.claim import ClaimCreate
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from datetime import datetime
from typing import Optional, List
import pandas as pd
from io import StringIO
from poapbot.db import POAPDatabase, DoesNotExist, ConflictError, BulkError
from poapbot.db.models import Claim, Event

from ..dependencies import get_db

router = APIRouter(
    prefix="/claims",
    tags=["claims"],
    dependencies=[Depends(get_db)]
)

@router.post(
    "/upload_claims",
    tags=['claims']
)
async def upload_claims(event_id: str, file: UploadFile = File(...), db: POAPDatabase = Depends(get_db)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=415, detail=f'File must be of type /text/csv, provided: {file.content_type}')
    try:
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to parse file: {e}')

    if 'link' not in df.columns:
        raise HTTPException(status_code=400, detail=f'List must have "link" column header')
    
    if 'username' not in df.columns:
        df['username'] = None

    claims = [ClaimCreate(username=row.username, event_id=event_id, link=row.link) for ix, row in df.iterrows()]
    try:
        claims = await db.create_claims_bulk(event_id, claims)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BulkError as e:
        raise HTTPException(status_code=400, detail={'count':len(e.errors), 'errors':e.errors[:100]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{id}",
    tags=['claims'],
    response_model=Claim
)
async def get_claim_by_id(id: str, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.get_claim_by_id(id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get(
    "/event/{event_id}",
    tags=['claims'],
    response_model=List[Claim]
)
async def get_claims_by_event_id(event_id: str, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.get_claims_by_event_id(event_id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "/",
    tags=['claims']
)
async def create_claim(claim: ClaimCreate, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.create_claim(claim)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete(
    "/{id}",
    tags=['claims']
)
async def delete_claim(id: str, db: POAPDatabase = Depends(get_db)):
    try:
        await db.delete_claim_by_id(id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put(
    "/{id}/clear_attendee",
    tags=['claims']
)
async def clear_claim_attendee(id: str, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.clear_claim_by_id(id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put(
    "/{id}/reserve",
    tags=['claims']
)
async def set_claim_by_id(id: str, username: str, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.set_claim_by_id(id, username)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.put(
    "/reserve",
    tags=['claims']
)
async def set_claim_by_event_id(event_id: str, username: str, db: POAPDatabase = Depends(get_db)):
    try:
        return await db.set_claim_by_event_id(event_id, username)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
