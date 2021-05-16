from asyncpraw import Reddit
from asyncpraw.models import Message, Redditor, Comment
import asyncio
from datetime import datetime
import logging
import ormar
import re
import yaml

from poapbot.db.models import Event, Claim, Attendee, Admin, RequestMessage, ResponseMessage
from poapbot.settings import POAPSettings
from poapbot.db import POAPDatabase, DoesNotExist

from .exceptions import NotStartedEvent, ExpiredEvent, NoClaimsAvailable, InvalidCode, InsufficientAccountAge, InsufficientKarma, UnauthorizedCommand

logger = logging.getLogger(__name__)

SETTINGS = POAPSettings.parse_obj(yaml.safe_load(open('settings.yaml','r'))['poap'])

CREATE_EVENT_PATTERN = re.compile(r'create_event (?P<id>\w+) (?P<name>\w+) (?P<code>\w+) (?P<start_date>[\w:-]+) (?P<expiry_date>[\w:-]+) (?P<minimum_age>\w+) (?P<minimum_karma>\w+)')
ADD_CLAIMS_PATTERN = re.compile(r'add_claims (?P<event_id>\w+) (?P<codes>(\w+,?)+)')

class RedditBot:

    def __init__(self, client: Reddit, db: POAPDatabase):
        self.client = client
        self.db = db

    async def reserve_claim(self, code: str, redditor: Redditor) -> Claim:
        try:
            event = await self.db.get_event_by_code(code)
        except DoesNotExist:
            raise InvalidCode

        try:
            return await self.db.get_claim_by_event_username(event.id, redditor.name)
        except DoesNotExist:
            pass

        if not event.started():
            raise NotStartedEvent(event)
        elif event.expired():
            raise ExpiredEvent(event)

        await redditor.load()
        age = (datetime.utcnow() - datetime.utcfromtimestamp(int(redditor.created_utc))).total_seconds() // 86400 # seconds in a day
        if redditor.comment_karma + redditor.link_karma < event.minimum_karma:
            raise InsufficientKarma(event)
        elif age < event.minimum_age:
            raise InsufficientAccountAge(event)

        try:
            return await self.db.set_claim_by_event_id(event.id, redditor.name)
        except DoesNotExist:
            raise NoClaimsAvailable(event)

    async def try_claim(self, code: str, message: Message, redditor: Redditor) -> Comment:
        claim = None
        try:
            claim = await self.reserve_claim(code, redditor)
            logger.debug(f'Received valid request from {redditor.name} for event {claim.event.id}, sending link {claim.link}')
            return await message.reply(f'Your claim link for {claim.event.name} is {claim.link}')
        except InvalidCode:
            logger.debug(f'Received request from {redditor.name} with invalid code {code}')
            return await message.reply(f'Invalid event code: {code}')
        except NotStartedEvent as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but event has not started')
            return await message.reply(f'Sorry, event {e.event.name} has not started yet')
        except ExpiredEvent as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but event has expired')
            return await message.reply(f'Sorry, event {e.event.name} has expired')
        except NoClaimsAvailable as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but no more claims are available')
            return await message.reply(f'Sorry, there are no more claims available for {e.event.name}')
        except InsufficientAccountAge as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but account is too young')
            return await message.reply(f'Sorry, your account is not old enough to be eligible')
        except InsufficientKarma as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but not enough karma')
            return await message.reply(f'Sorry, your account does not have enough karma to be eligible')
        except Exception as e:
            logger.error(e, exc_info=True)
            return await message.reply(f'Bot encountered an unrecognized error :(')

    async def is_admin(self, redditor: Redditor):
        try:
            return await self.db.get_admin_by_username(redditor.name) is not None
        except DoesNotExist:
            return False
    
    async def create_event(self, message: Message, redditor: Redditor) -> Comment:
        if not await self.is_admin(redditor):
            logger.debug(f'Received request from {redditor.name} to create_event, but they are unauthorized')
            return await message.reply('You are unauthorized to execute this command')

        command_data = CREATE_EVENT_PATTERN.match(message.body)
        if not command_data:
            logger.debug(f'Received request from {redditor.name} to create_event, but command was malformed: {message.body}')
            return await message.reply(
                """Your create_event command was malformed, must be of the format: \n\n"""
                """'create_event event_id event_name event_code start_date end_date minimum_age minimum_karma'\n\n"""
                """Date strings must be in UTC and ISO8601 formatted, eg. 2021-05-01T00:00:00"""
            )
        else:
            command_data = command_data.groupdict()

        existing_event = await self.db.get_event_by_id(command_data['id'])
        if existing_event:
            logger.debug(f'Received request to create event, but an event with the provided id already exists')
            return await message.reply(f'Failed to create event: An event with id {command_data["id"]} already exists')

        try:
            event = await self.db.create_event(**command_data)
            logger.debug('Received request to create event, successful')
            return await message.reply(f'Successfully created event {event.name}')
        except Exception as e:
            logger.error(f'Received request to create event, but it failed: {e}', exc_info=True)
            return await message.reply(f'Failed to create event: {e}')

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

        request_message = await self.db.get(RequestMessage, secondary_id=message.id)
        if request_message:
            logger.debug(f'Request message {request_message.secondary_id} has already been processed, skipping')
            await message.mark_read()
            return

        await self.db.create_request_message(
            message.id,
            redditor.name,
            message.created_utc,
            message.subject,
            message.body
        )

        if code == 'create_event':
            comment = await self.create_event(message, redditor)
        else:
            comment = await self.try_claim(code, message, redditor)

        await message.mark_read()
        await self.db.create_response_message(
            comment.id, 
            comment.author.name, 
            comment.created_utc, 
            comment.body
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
