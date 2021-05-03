from asyncpraw import Reddit
from asyncpraw.models import Message
import asyncio

from models.event import Event, AttendanceType

class RedditBot:

    def __init__(self, client: Reddit):
        self.client = client
        
        self.run_task = None

    async def message_handler(self, message: Message):
        print(message)
        if message.body and 'ping' in message.body.lower():
            await message.reply('pong')
        await message.mark_read()

    async def run(self):
        async for item in self.client.inbox.stream():
            if isinstance(item, Message):
                asyncio.create_task(self.message_handler(item))