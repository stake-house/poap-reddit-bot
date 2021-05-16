from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional

from poapbot.scraper import RedditScraper

from ..dependencies import get_scraper

router = APIRouter(
    prefix="/scrape",
    tags=["scrape"],
    dependencies=[Depends(get_scraper)]
)

@router.get("/get_usernames_by_submission")
async def get_usernames_by_submission(submission_id: str, traverse: bool = False, scraper: RedditScraper = Depends(get_scraper)):
    try:
        comments = await scraper.get_comments_by_submission_id(submission_id, traverse)
        return list(set([c.author.name for c in comments if c.author]))
    except Exception as e:
        # todo better exception handling
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_usernames_by_comment")
async def get_usernames_by_comment(comment_id: str, traverse: bool = False, scraper: RedditScraper = Depends(get_scraper)):
    try:
        comments = await scraper.get_comments_by_comment_id(comment_id, traverse)
        return list(set([c.author.name for c in comments if c.author]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))