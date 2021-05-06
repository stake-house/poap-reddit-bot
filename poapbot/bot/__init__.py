from asyncpraw import Reddit
from asyncpraw.models import Message, Redditor
import asyncio
from datetime import datetime
import logging
import ormar

from ..models import Event, Claim, Attendee, RequestMessage, ResponseMessage
from ..store import EventDataStore
from .exceptions import ExpiredEvent, NoClaimsAvailable, InvalidCode, InsufficientAccountAge, InsufficientKarma

logger = logging.getLogger(__name__)

class RedditBot:

    def __init__(self, client: Reddit, store: EventDataStore):
        self.client = client
        self.store = store

    async def reserve_claim(self, code: str, redditor: Redditor) -> Claim:
        event = await self.store.get(Event, code=code)
        if not event:
            raise InvalidCode
        elif event.expired():
            raise ExpiredEvent(event)

        existing_claim = await self.store.get_filter(Claim, attendee__username=redditor.name, event__id__exact=event.id)
        if existing_claim:
            return existing_claim

        await redditor.load()
        age = (datetime.utcnow() - datetime.utcfromtimestamp(int(redditor.created_utc))).total_seconds() // 86400 # seconds in a day
        if redditor.comment_karma + redditor.link_karma < event.minimum_karma:
            raise InsufficientKarma(event)
        elif age < event.minimum_age:
            raise InsufficientAccountAge(event)

        async with self.store.db.transaction():
            try:
                claim = await self.store.get_filter_first(Claim, reserved__exact=False, event__id__exact=event.id)
            except ormar.exceptions.NoMatch:
                raise NoClaimsAvailable(event)
            attendee = await self.store.get_or_create(Attendee, username=redditor.name)
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

        request_message = await self.store.get(RequestMessage, secondary_id=message.id)
        if request_message:
            logger.debug(f'Request message {request_message.secondary_id} has already been processed, skipping')
            await message.mark_read()
            return

        request_message = await self.store.create(
            RequestMessage, 
            secondary_id=message.id, 
            username=redditor.name, 
            created=message.created_utc, 
            subject=message.subject, 
            body=message.body
        )

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
        except InsufficientAccountAge as e:
            comment = await message.reply(f'Sorry, your account is not old enough to be eligible')
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but account is too young')
        except InsufficientKarma as e:
            comment = await message.reply(f'Sorry, your account does not have enough karma to be eligible')
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but not enough karma')

        await message.mark_read()
        await self.store.create(
            ResponseMessage,
            secondary_id=comment.id, 
            username=comment.author.name, 
            created=comment.created_utc, 
            body=comment.body, 
            claim=claim
        )

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