from fastapi import FastAPI, Request, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi_crudrouter import OrmarCRUDRouter as CRUDRouter
import asyncio
import sqlalchemy
import ormar
import yaml
from io import StringIO
import asyncpraw
import pandas as pd
from datetime import datetime
from typing import Optional

from poapbot.models.settings import RedditSettings, DBSettings, FastAPISettings

SETTINGS = yaml.safe_load(open('settings.yaml', 'r'))
REDDIT_SETTINGS = RedditSettings.parse_obj(SETTINGS['reddit'])
DB_SETTINGS = DBSettings.parse_obj(SETTINGS['db'])
API_SETTINGS = FastAPISettings.parse_obj(SETTINGS['fastapi'])

from poapbot.scraper import RedditScraper
from poapbot.bot import RedditBot
from poapbot.models import metadata, database, Event, Attendee, Claim

engine = sqlalchemy.create_engine(DB_SETTINGS.url)
metadata.create_all(engine)

app = FastAPI(
    title=API_SETTINGS.title,
    version=API_SETTINGS.version,
    openapi_tags=API_SETTINGS.openapi_tags
)
app.include_router(CRUDRouter(schema=Event, prefix='event'))
app.include_router(CRUDRouter(schema=Attendee, prefix='attendee'))
app.include_router(CRUDRouter(schema=Claim, prefix='claim'))
app.state.database = database
                
@app.on_event('startup')
async def startup_event():
    db = app.state.database
    if not db.is_connected:
        await db.connect()

    reddit_client = asyncpraw.Reddit(
        username=REDDIT_SETTINGS.auth.username,
        password=REDDIT_SETTINGS.auth.password.get_secret_value(),
        client_id=REDDIT_SETTINGS.auth.client_id,
        client_secret=REDDIT_SETTINGS.auth.client_secret.get_secret_value(),
        user_agent=REDDIT_SETTINGS.auth.user_agent
    )
    
    bot = RedditBot(reddit_client)
    asyncio.create_task(bot.run())

    app.state.scraper = RedditScraper(reddit_client)
    app.state.bot = bot

@app.on_event("shutdown")
async def shutdown():
    db = app.state.database
    if db.is_connected:
        await db.disconnect()

@app.post(
    "/admin/event",
    description="Create Event",
    tags=['admin'],
    response_model=Event
)
async def create_event(request: Request, id: str, name: str, code: str, expiry_date: datetime, description: Optional[str] = ""):
    existing_event = await Event.objects.get_or_none(pk=id)
    if existing_event:
        raise HTTPException(status_code=409, detail=f'Event with id "{id}" already exists')
    else:
        event = Event(id=id, name=name, code=code, description=description, expiry_date=expiry_date)
        await event.save()
        return event

@app.post(
    "/admin/grant_claim",
    tags=['admin'],
    response_model=Claim
)
async def grant_claim(request: Request, event_id: str, username: str, link: str):
    try:
        event = await Event.objects.get(pk=event_id)
    except ormar.exceptions.NoMatch:
        raise HTTPException(status_code=404, detail=f'Event with id "{event_id}" does not exist')
    try:
        attendee = await Attendee.objects.get(pk=username)
    except ormar.exceptions.NoMatch:
        raise HTTPException(status_code=404, detail=f'Attendee with username "{username}" does not exist')
    try:
        claim = Claim(event=event, attendee=attendee, link=link)
        await claim.save()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post(
    "/admin/upload_claims",
    tags=['admin']
)
async def upload_claims(request: Request, event_id: str, file: UploadFile = File(...)):
    try:
        event = await Event.objects.get(pk=event_id)
    except ormar.exceptions.NoMatch:
        raise HTTPException(status_code=404, detail=f'Event with id "{event_id}" does not exist')

    if file.content_type != 'text/csv':
        raise HTTPException(status_code=415, detail=f'File must be of type /text/csv, provided: {file.content_type}')
    try:
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to parse file: {e}')

    if any([c not in df.columns for c in ['username','link']]):
        raise HTTPException(status_code=400, detail=f'List must contain "username" and "link" columns')
    
    df['username'] = df['username'].apply(lambda x: x.lower())
    usernames = df['username'].tolist()
    claim_map = df.set_index('username')['link'].to_dict()

    existing_attendees = await Attendee.objects.filter(id__in=usernames).all()
    existing_claims = await Claim.objects.filter(ormar.and_(event__id__exact=event_id, attendee__username__in=usernames)).all()
    existing_claim_usernames = [c.attendee.username for c in existing_claims]
    
    new_attendees = [Attendee(id=username) for username in usernames if username not in [p.id for p in existing_attendees]]
    await Attendee.objects.bulk_create(new_attendees)

    attendees = existing_attendees + new_attendees

    for attendee in attendees:
        if attendee.id not in existing_claim_usernames:
            claim = Claim(event=event, attendee=attendee, link=claim_map[attendee.id])
            await claim.save()

    return True

@app.get(
    "/scrape/get_usernames_by_submission",
    tags=['scrape']
)
async def get_usernames_by_submission(request: Request, submission_id: str, traverse: bool = False):
    try:
        comments = await request.app.state.scraper.get_comments_by_submission_id(submission_id, traverse)
        return list(set([c.author.name for c in comments if c.author]))
    except Exception as e:
        # todo better exception handling
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/scrape/get_usernames_by_comment",
    tags=['scrape']
)
async def get_usernames_by_comment(request: Request, comment_id: str, traverse: bool = False):
    try:
        comments = await request.app.state.scraper.get_comments_by_comment_id(comment_id, traverse)
        return list(set([c.author.name for c in comments if c.author]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))