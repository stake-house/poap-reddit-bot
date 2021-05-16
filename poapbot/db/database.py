from poapbot.db.models import attendee
from ormar import Model
from ormar.exceptions import NoMatch
from .exceptions import BulkError, DoesNotExist, ConflictError, BulkError
from .models import *
from . import database
from datetime import datetime
from typing import List, Union, Dict, Tuple

class POAPDatabase:

    def __init__(self):
        self.db = database

    async def connect(self):
        if not self.db.is_connected:
            await self.db.connect()

    async def close(self):
        if self.db.is_connected:
            await self.db.disconnect()

    ## Claims

    async def create_claim(self, claim: ClaimCreate) -> Claim:
        event = await self.get_event_by_id(claim.event_id)
        if claim.username:
            try:
                attendee = await self.get_attendee_by_username(claim.username)
            except DoesNotExist:
                attendee = await self.create_attendee_by_username(claim.username)
        else:
            attendee = None
        db_claim = Claim(event=event, attendee=attendee, link=claim.link, reserved=True if attendee else False)
        await db_claim.save()
        return Claim.parse_obj(db_claim)

    async def set_claim_by_id(self, id: str, username: str) -> Claim:
        async with self.db.transaction():
            claim = await self.get_claim_by_id(id)
            try:
                existing_claim = await self.get_claim_by_event_username(claim.event.id, username)
                if existing_claim:
                    raise ConflictError(f'Username {username} already has claim for event {claim.event.id}: Claim {existing_claim.id}')
            except DoesNotExist:
                pass
            attendee = await Attendee.objects.get_or_create(username=username)
            claim.attendee = attendee
            claim.reserved = True
            await claim.update()
            return claim

    async def get_claim_by_id(self, id: str) -> Claim:
        try:
            return await Claim.objects.get(id=id)
        except NoMatch as e:
            raise DoesNotExist(f'Claim with id {id} does not exist') from e

    async def get_claim_by_event_username(self, event_id: str, username: str) -> Claim:
        try:
            return await Claim.objects.filter(attendee__username__exact=username, event__id__exact=event_id).get()
        except NoMatch as e:
            raise DoesNotExist(f'Claim by username {username} for event {event_id} does not exist') from e

    async def delete_claim_by_id(self, id: str) -> None:
        claim = await self.get_claim_by_id(id)
        await claim.delete()

    async def clear_claim_by_id(self, id: str) -> Claim:
        claim = await self.get_claim_by_id(id)
        async with self.db.transaction():
            claim.remove(claim.attendee, 'attendee')
            claim.reserved = False
            await claim.update()

    async def set_claim_by_event_id(self, event_id: str, username: str) -> Claim:
        async with self.db.transaction():
            try:
                existing_claim = await self.get_claim_by_event_username(event_id, username)
                if existing_claim:
                    raise ConflictError(f'Username {username} already has claim for event {event_id}: Claim {existing_claim.id}')
            except DoesNotExist:
                pass
            try:
                claim = await Claim.objects.filter(reserved__exact=False, event__id__exact=event_id).first()
            except NoMatch:
                raise DoesNotExist(f'No claims available for event {event_id}')
            try:
                attendee = await self.get_attendee_by_username(username)
            except DoesNotExist:
                attendee = await self.create_attendee_by_username(username)
            claim.attendee = attendee
            claim.reserved = True
            await claim.update()
            return claim

    async def get_claims(self, select_related: List[str] = None, offset: int = 0, limit: int = 0) -> List[Claim]:
        try:
            q = Claim.objects.offset(offset)
            if select_related:
                q = q.select_related(select_related)
            if limit > 0:
                q = q.limit(limit)
            return await q.all()
        except NoMatch:
            return []

    async def get_claims_by_event_id(self, event_id: str, select_related: List[str] = None, offset: int = 0, limit: int = 0) -> List[Claim]:
        try:
            q = Claim.objects.filter(event__code__id=event_id).offset(offset)
            if select_related:
                q = q.select_related(select_related)
            if limit > 0:
                q = q.limit(limit)
            return await q.all()
        except NoMatch:
            return []

    ## Events
    
    async def create_event(self, event: EventCreate) -> Event:
        try:
            event = await self.get_event_by_id(event.id)
            if event:
                raise ConflictError(f'Event with id {event.id} already exists')
        except DoesNotExist:
            event = Event(**event.dict())
            await event.save()
            return event

    async def update_event(self, event_update: EventUpdate) -> Event:
        event = await self.get_event_by_id(event_update.id)
        await event.update(**event_update.dict(exclude_none=True))
        return event
    
    async def get_event_by_id(self, id: str) -> Event:
        try:
            return await Event.objects.get(id=id)
        except NoMatch as e:
            raise DoesNotExist(f'Event {id} does not exist') from e

    async def get_event_by_code(self, code: str) -> Event:
        try:
            return await Event.objects.get(code__exact=code)
        except NoMatch as e:
            raise DoesNotExist(f'Event with code {code} does not exist') from e

    async def get_events(self, offset: int = 0, limit: int = 0) -> List[Event]:
        try:
            q = Event.objects.offset(offset)
            if limit > 0:
                q = q.limit(limit)
            return await q.all()
        except NoMatch:
            return []

    async def delete_event_by_id(self, id: str) -> Event:
        event = await self.get_event_by_id(id)
        await event.delete()
        return event

    ## Attendees

    async def create_attendee_by_username(self, username: str) -> Attendee:
        attendee = Attendee(username=username)
        await attendee.save()
        return attendee

    async def get_attendee_by_id(self, id: str) -> Attendee:
        try:
            return await Attendee.objects.get(id=id)
        except NoMatch as e:
            raise DoesNotExist(f'Attendee with id {id} does not exist') from e

    async def get_attendee_by_username(self, username: str) -> Attendee:
        try:
            return await Attendee.objects.get(username__exact=username)
        except NoMatch as e:
            raise DoesNotExist(f'Attendee with username {username} does not exist') from e
    
    async def get_attendees(self, offset: int = 0, limit: int = 0) -> List[Attendee]:
        try:
            q = Attendee.objects.offset(offset)
            if limit > 0:
                q = q.limit(limit)
            return await q.all()
        except NoMatch:
            return []

    ## Admins

    async def create_admin(self, admin: AdminCreate) -> Admin:
        try:
            db_admin = await self.get_admin_by_username(admin.username)
            if db_admin:
                raise ConflictError(f'Admin with username {admin.username} already exists')
        except DoesNotExist:
            db_admin = Admin(**admin.dict())
            await db_admin.save()
            return db_admin

    async def get_admin_by_id(self, id: str) -> Admin:
        try:
            return await Admin.objects.get(id=id)
        except NoMatch as e:
            raise DoesNotExist(f'Admin with id {id} does not exist') from e

    async def get_admin_by_username(self, username: str) -> Admin:
        try:
            return await Admin.objects.get(username__exact=username)
        except NoMatch as e:
            raise DoesNotExist(f'Admin with username {username} does not exist') from e

    ## Request Messages

    async def create_request_message(self, secondary_id: str, username: str, created: datetime, subject: str, body: str) -> RequestMessage:
        request_message = RequestMessage(
            secondary_id=secondary_id,
            username=username,
            created=created,
            subject=subject,
            body=body
        )
        await request_message.save()
        return request_message

    async def get_request_message_by_id(self, id: str) -> RequestMessage:
        try:
            return await RequestMessage.objects.get(id=id)
        except NoMatch as e:
            raise DoesNotExist(f'Request message with id {id} does not exist') from e

    ## Response Messages

    async def create_response_message(self, secondary_id: str, username: str, created: datetime, body: str) -> ResponseMessage:
        response_message = ResponseMessage(
            secondary_id=secondary_id,
            username=username,
            created=created,
            body=body
        )
        await response_message.save()
        return response_message

    async def get_response_message_by_id(self, id: str) -> ResponseMessage:
        try:
            return await ResponseMessage.objects.get(id=id)
        except NoMatch as e:
            raise DoesNotExist(f'Response message with id {id} does not exist') from e

    ## Bulk

    async def create_claims_bulk(self, event_id: str, new_claims: List[ClaimCreate]) -> List[Claim]:
        event = await self.get_event_by_id(event_id)
        existing_claims = await self.get_claims_by_event_id(event_id)
        existing_links = set([c.link for c in existing_claims])
        existing_usernames = set([c.attendee.username for c in existing_claims if c.attendee])

        errors = []
        for index, claim in enumerate(new_claims):
            if claim.username in existing_usernames:
                errors.append({'index':index, 'reason':f'Username {claim.username} already has reserved claim'})
            elif claim.link in existing_links:
                errors.append({'index':index, 'reason':f'Claim link {claim.link} already exists'})
            elif not claim.link:
                errors.append({'index':index, 'reason':f'Invalid link {claim.link}'})
        
        if errors:
            raise BulkError(errors)

        attendees = []
        claims = []
        for new_claim in new_claims:
            if new_claim.username:
                try:
                    attendee = await self.get_attendee_by_username(new_claim.username)
                except DoesNotExist:
                    attendee = await self.create_attendee_by_username(new_claim.username)
                attendees.append(attendee)
            else:
                attendee = None

            claim = Claim(attendee=attendee, event=event, link=new_claim.link, reserved=True if attendee else False)
            claims.append(claim)
            
        async with self.db.transaction():
            await Attendee.objects.bulk_create(attendees)
            await Claim.objects.bulk_create(claims)

        return claims
