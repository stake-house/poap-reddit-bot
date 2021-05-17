from poapbot.db.exceptions import ConflictError
from asyncpraw import Reddit
from asyncpraw.models import Message, Redditor, Comment
import asyncio
from datetime import datetime
import logging
import yaml
from typing import Dict, List

from poapbot.db.models import *
from poapbot.settings import POAPSettings
from poapbot.db import POAPDatabase, DoesNotExist

from .exceptions import NotStartedEvent, ExpiredEvent, NoClaimsAvailable, InvalidCode, InsufficientAccountAge, InsufficientKarma, UnauthorizedCommand
from .commands import *

logger = logging.getLogger(__name__)

SETTINGS = POAPSettings.parse_obj(yaml.safe_load(open('settings.yaml','r'))['poap'])

class RedditBot:

    def __init__(self, client: Reddit, db: POAPDatabase):
        self.client = client
        self.db = db

        self.command_handlers = {
            CreateEventCommand: self.create_event,
            UpdateEventCommand: self.update_event,
            CreateClaimsCommand: self.create_claims
        }

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

    async def try_claim(self, code: str, message: Message, redditor: Redditor):
        claim = None
        try:
            claim = await self.reserve_claim(code, redditor)
            logger.debug(f'Received valid request from {redditor.name} for event {claim.event.id}, sending link {claim.link}')
            await self.send_response(message, f'Your claim link for {claim.event.name} is {claim.link}')
        except InvalidCode:
            logger.debug(f'Received request from {redditor.name} with invalid code {code}')
            await self.send_response(message, f'Invalid event code: {code}')
        except NotStartedEvent as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but event has not started')
            await self.send_response(message, f'Sorry, event {e.event.name} has not started yet')
        except ExpiredEvent as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but event has expired')
            await self.send_response(message, f'Sorry, event {e.event.name} has expired')
        except NoClaimsAvailable as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but no more claims are available')
            await self.send_response(message, f'Sorry, there are no more claims available for {e.event.name}')
        except InsufficientAccountAge as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but account is too young')
            await self.send_response(message, f'Sorry, your account is not old enough to be eligible')
        except InsufficientKarma as e:
            logger.debug(f'Received request from {redditor.name} for event {e.event.id}, but not enough karma')
            await self.send_response(message, f'Sorry, your account does not have enough karma to be eligible')
        except Exception as e:
            logger.error(e, exc_info=True)
            await self.send_response(message, f'Bot encountered an unrecognized error :(')

    async def is_admin(self, redditor: Redditor):
        try:
            return await self.db.get_admin_by_username(redditor.name) is not None
        except DoesNotExist:
            return False
    
    async def create_event(self, message: Message, command_data: Dict[str, str]):
        try:
            event = await self.db.create_event(EventCreate(**command_data))
            await self.send_response(message, f'Successfully created event: {event.json()}')
        except Exception as e:
            await self.send_response(message, f'Failed to create event: {e}')

    async def update_event(self, message: Message, command_data: Dict[str, str]):
        try:
            event = await self.db.update_event(EventUpdate(**command_data))
            await self.send_response(message, f'Successfully updated event: {event.json()}')
        except Exception as e:
            await self.send_response(message, f'Failed to update event: {e}')

    async def create_claims(self, message: Message, command_data: Dict[str, str]):
        try:
            event_id = command_data['event_id']
            event = await self.db.get_event_by_id(event_id)
            new_claims = [ClaimCreate(event_id=event_id, link=f'{SETTINGS.url}{code}') for code in command_data['codes'].split(',')]
            claims = await self.db.create_claims_bulk(event_id, new_claims)
            await self.send_response(message, f'Successfully added {len(claims)} claims to event {event.name}')
        except Exception:
            logger.error(f'Failed to add claims', exc_info=True)
            await self.send_response(message, 'Failed to add claims')

    async def process_command(self, message: Message, command: Command):
        command_data = command.pattern.match(message.body)
        if not command_data:
            logger.debug(f'Received {command.name} command, but was malformed: {message.body}')
            await self.send_response(message, f'{command.name} command was malformed, must be of the format: \n\n{command.example}')
        else:
            try:
                await self.command_handlers[command](message, command_data.groupdict())
            except:
                logger.error('Failed to parse command', exc_info=True)

    async def send_response(self, message: Message, response: str):
        response_message = await message.reply(response)
        await self.db.create_response_message(
            response_message.id, 
            response_message.author.name, 
            response_message.created_utc, 
            response_message.body
        )
    
    async def message_handler(self, message: Message):
        redditor = message.author
        if not redditor:
            logger.info('Received message from shadow-banned or deleted user, skipping')
            await message.mark_read()
            return

        if message.body.lower() == 'ping':
            await self.send_response(message, 'pong')
            await message.mark_read()
            logger.info('Received ping, sending pong')
            return
        elif redditor.name == 'reddit':
            await message.mark_read()
            logger.info('Received message from reddit, skipping')
            return

        try:
            request_message = await self.db.get_request_message_by_id(message.id)
            if request_message:
                logger.debug(f'Request message {request_message.secondary_id} has already been processed, skipping')
                await message.mark_read()
                return
        except DoesNotExist:
            pass

        await self.db.create_request_message(
            message.id,
            redditor.name,
            message.created_utc,
            message.subject,
            message.body
        )

        code = message.body.split(' ')[0].lower()
        command = next(filter(lambda cmd: cmd.name == code, self.command_handlers.keys()), None)
        if command:
            if not await self.is_admin(redditor):
                logger.debug(f'Received request from {redditor.name} to {command.name}, but they are unauthorized')
                await self.send_response(message, 'You are unauthorized to execute command: {command.name}')
            else:
                await self.process_command(message, command)
        else:
            await self.try_claim(code, message, redditor)

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
                logger.error('Encountered error in run loop', exc_info=True)
            await asyncio.sleep(1)
