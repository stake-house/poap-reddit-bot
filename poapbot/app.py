from fastapi import FastAPI
import asyncio
import yaml
import logging.config
import asyncpraw

from poapbot.settings import RedditSettings, FastAPISettings
from poapbot.db import POAPDatabase
from poapbot.bot import RedditBot
from poapbot.scraper import RedditScraper
from poapbot.routers import admin, claim, event, export, scrape

SETTINGS = yaml.safe_load(open('settings.yaml', 'r'))
REDDIT_SETTINGS = RedditSettings.parse_obj(SETTINGS['reddit'])
API_SETTINGS = FastAPISettings.parse_obj(SETTINGS['fastapi'])

app = FastAPI(
    title=API_SETTINGS.title,
    version=API_SETTINGS.version,
    openapi_tags=API_SETTINGS.openapi_tags
)
app.include_router(admin.router)
app.include_router(claim.router)
app.include_router(event.router)
app.include_router(export.router)
app.include_router(scrape.router)

logging.config.fileConfig('logging.conf', disable_existing_loggers=True)
logger = logging.getLogger(__name__)

app.state.db = POAPDatabase()
                
@app.on_event('startup')
async def startup_event():
    await app.state.db.connect()

    reddit_client = asyncpraw.Reddit(
        username=REDDIT_SETTINGS.auth.username,
        password=REDDIT_SETTINGS.auth.password.get_secret_value(),
        client_id=REDDIT_SETTINGS.auth.client_id,
        client_secret=REDDIT_SETTINGS.auth.client_secret.get_secret_value(),
        user_agent=REDDIT_SETTINGS.auth.user_agent
    )
    
    bot = RedditBot(reddit_client, app.state.db)
    asyncio.create_task(bot.run())

    app.state.scraper = RedditScraper(reddit_client)
    app.state.bot = bot

@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()
