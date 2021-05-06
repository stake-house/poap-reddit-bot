from asyncpraw import Reddit
from asyncpraw.models import Message, Redditor
import asyncio
from datetime import datetime
import logging
import ormar

from ..models import database, Event, Claim, Attendee, RequestMessage, ResponseMessage
from .exceptions import ExpiredEvent, NoClaimsAvailable, InvalidCode

logger = logging.getLogger(__name__)

class RedditBot:

    def __init__(self, client: Reddit):
        self.client = client

    async def reserve_claim(self, code: str, redditor: Redditor) -> Claim:
        event = await Event.objects.get_or_none(code=code)
        if not event:
            raise InvalidCode
        elif event.expired():
            raise ExpiredEvent(event)

        existing_claim = await Claim.objects.filter(attendee__username=redditor.name, event__id__exact=event.id).get_or_none()
        if existing_claim:
            return existing_claim

        async with database.transaction():
            try:
                claim = await Claim.objects.filter(reserved__exact=False, event__id__exact=event.id).first()
            except ormar.exceptions.NoMatch:
                raise NoClaimsAvailable(event)
            attendee = await Attendee.objects.get_or_create(username=redditor.name)
            claim.attendee = attendee
            claim.reserved = True
            await claim.update()
        return claim

    async def message_handler(self, message: Message):
        redditor = message.author
        if not redditor:
            logger.info('Received message from shadow-banned or deleted user, skipping')
            await message.mark_read()
            return

        code = message.body.split(' ')[0].lower()

        if code == 'ping':
            await message.reply('pong')
            await message.mark_read()
            logger.info('Received ping, sending pong')
            return
        elif redditor.name == 'reddit':
            await message.mark_read()
            logger.info('Received message from reddit, skipping')
            return

        request_message = await RequestMessage.objects.get_or_none(secondary_id=message.id)
        if request_message:
            logger.debug(f'Request message {request_message.secondary_id} has already been processed, skipping')
            await message.mark_read()
            return

        request_message = RequestMessage(
            secondary_id=message.id, 
            username=redditor.name, 
            created=message.created_utc, 
            subject=message.subject, 
            body=message.body
        )
        await request_message.save()

        claim = None
        try:
            claim = await self.reserve_claim(code, redditor)
            comment = await message.reply(f'Your claim link for {claim.event.name} is {claim.link}')
            logger.debug(f'Received valid request from {redditor.name} for event {claim.event.id}, sending link {claim.link}')
        except InvalidCode:
            comment = await message.reply(f'Invalid event code: {code}')
            logger.debug(f'Received request from {redditor.name} with invalid code {code}')
        except ExpiredEvent as e:
            comment = await message.reply(f'Sorry, event {e.event.name} has expired')
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but event has expired')
        except NoClaimsAvailable as e:
            comment = await message.reply(f'Sorry, there are no more claims available for {e.event.name}')
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but no more claims are available')

        await message.mark_read()
        response_message = ResponseMessage(secondary_id=comment.id, username=comment.author.name, created=comment.created_utc, body=comment.body, claim=claim)
        await response_message.save()

    async def run(self):
        while True:
            try:
                async for item in self.client.inbox.stream():
                    if isinstance(item, Message):
                        await self.message_handler(item)
            except asyncio.CancelledError:
                return
            except:
                logger.error('Encountered error in run loop', exc_info=True)
            await asyncio.sleep(1)