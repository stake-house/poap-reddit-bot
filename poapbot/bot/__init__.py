from asyncpraw import Reddit
from asyncpraw.models import Message
import asyncio
from datetime import datetime
import logging
import ormar

from ..models import database, Event, Claim, Attendee, RequestMessage

logger = logging.getLogger(__name__)

class RedditBot:

    def __init__(self, client: Reddit):
        self.client = client

    async def message_handler(self, message: Message):
        username = message.author.name.lower() if message.author else None
        code = message.body.split(' ')[0].lower()

        if code == 'ping':
            await message.reply('pong')
            await message.mark_read()
            logger.info('Received ping, sending pong')
            return
        elif username == 'reddit':
            await message.mark_read()
            logger.info('Received message from reddit, skipping')
            return

        request_message = await RequestMessage.objects.get_or_none(id=message.id)
        if request_message:
            logger.debug(f'Request message {request_message.id} has already been processed, skipping')
            await message.mark_read()
            return
        else:
            request_message = RequestMessage(
                id=message.id, 
                username=username, 
                created=message.created_utc, 
                subject=message.subject, 
                body=message.body
            )
            await request_message.save()

        event = await Event.objects.get_or_none(code=code)
        if event:
            expired = event.expired()
            claim = await Claim.objects.filter(ormar.and_(attendee__username__exact=username, event__id__exact=event.id)).get_or_none()
            if claim:
                comment = await message.reply(f'Your claim link for {claim.event.name} is {claim.link}')
            elif not expired:
                claim = await Claim.objects.filter(ormar.and_(attendee__id__isnull=True, reserved__exact=False, event__id__exact=event.id)).get_or_none()
                if claim:
                    async with database.transaction():
                        attendee = await Attendee.objects.get_or_create(username=username)
                        await event.attendees.add(attendee)
                        claim.attendee = attendee
                        claim.reserved = True
                        await claim.update()
                    comment = await message.reply(f'Your claim link for {claim.event.name} is {claim.link}')
                else:
                    comment = await message.reply(f'Sorry, there are no more claims available for {event.name}')
            elif expired:
                comment = await message.reply(f'Sorry, event {event.name} has expired')
        else:
            comment = await message.reply(f'Invalid event code: {code}')

        await message.mark_read()

    async def run(self):
        while True:
            try:
                async for item in self.client.inbox.stream():
                    if isinstance(item, Message):
                        await self.message_handler(item)
            except asyncio.CancelledError:
                return
            except:
                logging.error('Encountered error in run loop', exc_info=True)
            await asyncio.sleep(1)