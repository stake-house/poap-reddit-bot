from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Optional
from io import StringIO
import pandas as pd
from poapbot.db import POAPDatabase
from poapbot.db.models import Claim, Event

from ..dependencies import get_db

router = APIRouter(
    prefix="/export",
    tags=["export"],
    dependencies=[Depends(get_db)]
)

def data_to_csv_response(data, filename):
    stream = StringIO(pd.DataFrame(data).fillna('').to_csv(index=False))
    response = StreamingResponse(stream, media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}-{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')}.csv"
    return response

@router.get("/events")
async def export_events(db: POAPDatabase = Depends(get_db)):
    events = await db.get_events()
    data = [event.dict() for event in events]
    return data_to_csv_response(data, 'events')

@router.get("/attendees")
async def export_attendees(db: POAPDatabase = Depends(get_db)):
    attendees = await db.get_attendees()
    data = [attendee.dict() for attendee in attendees]
    return data_to_csv_response(data, 'attendees')

@router.get("/claims")
async def export_claims(db: POAPDatabase = Depends(get_db)):
    claims = await db.get_claims(select_related=['attendee'])
    data = []
    for claim in claims:
        data.append(dict(
            id=claim.id,
            event_id=claim.event.id,
            reserved=claim.reserved,
            link=claim.link,
            username=claim.attendee.username if claim.attendee else ''
        ))
    return data_to_csv_response(data, 'claims')

@router.get("/claims/{event_id}")
async def export_claims_by_event(event_id: str, db: POAPDatabase = Depends(get_db)):
    claims = await db.get_claims_by_event_id(event_id, select_related=['attendee'])
    data = []
    for claim in claims:
        data.append(dict(
            id=claim.id,
            event_id=claim.event.id,
            reserved=claim.reserved,
            link=claim.link,
            username=claim.attendee.username if claim.attendee else ''
        ))
    return data_to_csv_response(data, f'claims-{event_id}')