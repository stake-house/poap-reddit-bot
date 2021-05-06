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
import logging

from poapbot.models.settings import RedditSettings, DBSettings, FastAPISettings

SETTINGS = yaml.safe_load(open('settings.yaml', 'r'))
REDDIT_SETTINGS = RedditSettings.parse_obj(SETTINGS['reddit'])
DB_SETTINGS = DBSettings.parse_obj(SETTINGS['db'])
API_SETTINGS = FastAPISettings.parse_obj(SETTINGS['fastapi'])

from poapbot.scraper import RedditScraper
from poapbot.bot import RedditBot
from poapbot.models import metadata, database, Event, Attendee, Claim, RequestMessage, ResponseMessage

engine = sqlalchemy.create_engine(DB_SETTINGS.url)
metadata.create_all(engine)

app = FastAPI(
    title=API_SETTINGS.title,
    version=API_SETTINGS.version,
    openapi_tags=API_SETTINGS.openapi_tags
)
app.include_router(CRUDRouter(schema=Event))
app.include_router(CRUDRouter(schema=Attendee))
app.include_router(CRUDRouter(schema=Claim))
app.include_router(CRUDRouter(schema=RequestMessage))
app.include_router(CRUDRouter(schema=ResponseMessage))
app.state.database = database

logging.config.fileConfig('logging.conf', disable_existing_loggers=True)
logger = logging.getLogger(__name__)
                
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

    if 'link' not in df.columns:
        raise HTTPException(status_code=400, detail=f'List must have "link" column header')
    elif 'username' not in df.columns:
        df['username'] = ''

    df = df.fillna('')
    df['username'] = df['username'].apply(lambda x: x.lower())
    
    existing_claims = await Claim.objects.filter(event__id__exact=event_id).all()
    existing_links = {c.link:c for c in existing_claims}
    existing_usernames = {c.attendee.username:c for c in existing_claims if c.attendee}

    success = 0
    rejected = []
    create_attendees = []
    create_claims = []
    for index, row in df.iterrows():
        if row.username in existing_usernames:
            rejected.append({'index':index, 'reason':f'Username {row.username} already has reserved claim'})
            continue
        elif row.link in existing_links:
            rejected.append({'index':index, 'reason':f'Claim link {row.link} already exists'})
            continue
        elif not row.link:
            rejected.append({'index':index, 'reason':f'Invalid link {row.link}'})
        
        if row.username:
            attendee = await Attendee.objects.get_or_none(username=row.username)
            if not attendee:
                attendee = Attendee(username=row.username)
                create_attendees.append(attendee)
        else:
            attendee = None

        claim = Claim(attendee=attendee, event=event, link=row.link, reserved=True if attendee else False)
        create_claims.append(claim)
        success += 1

    async with request.app.state.database.transaction():
        await Attendee.objects.bulk_create(create_attendees)
        await Claim.objects.bulk_create(create_claims)
    
    return {
        'success': success,
        'rejected': rejected if (len(rejected) <= 100) else len(rejected)
    }

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