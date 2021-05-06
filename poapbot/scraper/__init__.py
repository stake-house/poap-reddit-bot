import asyncpraw
import asyncio

class RedditScraper:

    def __init__(self, client: asyncpraw.Reddit, concurrency: int = 8):
        self.client = client
        self.concurrency = concurrency
        self.sem = asyncio.Semaphore(concurrency)
    
    async def get_comments_by_comment_id(self, comment_id: str, traverse: bool = False):
        async with self.sem:
            comment = await self.client.comment(comment_id)

            await comment.refresh()
            comments = comment.replies
            await comments.replace_more(limit=None)
            if traverse:
                comments = await comments.list()
            else:
                comments = list(comments)
            comments.append(comment)
            return comments
    
    async def get_comments_by_submission_id(self, submission_id: str, traverse: bool = False):
        async with self.sem:
            submission = await self.client.submission(submission_id, lazy=True)
            comments = await submission.comments()
            await comments.replace_more(limit=None)
            if traverse:
                comments = await comments.list()
            return comments