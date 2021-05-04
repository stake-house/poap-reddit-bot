from asyncpraw import Reddit
from asyncpraw.models import Message
import asyncio
from datetime import datetime
import logging

from models import Claim, RequestMessage

class RedditBot:

    def __init__(self, client: Reddit):
        self.client = client

    async def message_handler(self, message: Message):
        request_message = await RequestMessage.objects.get_or_none(id=message.id)
        if not request_message:
            request_message = RequestMessage(
                id=message.id, 
                author=message.author.name, 
                created=message.created_utc, 
                subject=message.subject, 
                body=message.body
            )
            await request_message.upsert()
        else:
            return

        if message.body and 'ping' in message.body.lower():
            await message.reply('pong')
        elif message.body:
            code = message.body.split(' ')[0].lower()
            claim = await Claim.objects.filter(event__id__exact=code, participant__id__exact=message.author.name.lower()).get_or_none()
            if claim:
                if claim.event.expiry_date < datetime.utcnow():
                    await message.reply(f'Sorry, your claim for {claim.event.id} has expired')
                else:
                    await message.reply(f'Your claim link for {claim.event.id} is {claim.link}')
                claim.notified = True
                await claim.update()
            else:
                await message.reply(f'Sorry, you do not have a claim for {code}')
        await message.mark_read()

    async def run(self):
        while True:
            try:
                async for item in self.client.inbox.stream():
                    if isinstance(item, Message):
                        asyncio.create_task(self.message_handler(item))
            except asyncio.CancelledError:
                return
            except:
                logging.error('Encountered error in run loop', exc_info=True)
            await asyncio.sleep(1)