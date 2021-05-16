from fastapi import Request
from poapbot.db import POAPDatabase
from poapbot.scraper import RedditScraper

async def get_db(request: Request) -> POAPDatabase:
    return request.app.state.db

async def get_scraper(request: Request) -> RedditScraper:
    return request.app.state.scraper
