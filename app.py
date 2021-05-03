from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
import asyncio
import yaml
import asyncpraw

from scraper import RedditScraper
from bot import RedditBot

from models.settings import RedditSettings
from asyncpraw.models import MoreComments

app = FastAPI()
                
@app.on_event('startup')
async def startup_event():
    settings = yaml.safe_load(open('settings.yaml', 'r'))

    reddit_settings = RedditSettings.parse_obj(settings['reddit'])
    reddit_client = asyncpraw.Reddit(
        username=reddit_settings.auth.username,
        password=reddit_settings.auth.password.get_secret_value(),
        client_id=reddit_settings.auth.client_id,
        client_secret=reddit_settings.auth.client_secret.get_secret_value(),
        user_agent=reddit_settings.auth.user_agent
    )
    
    bot = RedditBot(reddit_client)
    asyncio.create_task(bot.run())

    app.state.scraper = RedditScraper(reddit_client)
    app.state.bot = bot

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