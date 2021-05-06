import pytest
import asyncio
from datetime import datetime
from poapbot.bot import RedditBot
from poapbot.bot.exceptions import NotStartedEvent, ExpiredEvent, NoClaimsAvailable, InvalidCode, InsufficientAccountAge, InsufficientKarma

@pytest.fixture
def bot(store):
    return RedditBot(None, store)

@pytest.mark.asyncio
async def test_reserve_claim_no_event(mocker, bot, dummy_event, dummy_redditor):
    mocker.patch.object(bot.store, 'get', return_value=None)
    with pytest.raises(InvalidCode):
        await bot.reserve_claim('invalid_code', dummy_redditor)

@pytest.mark.asyncio
async def test_reserve_claim_event_not_started(mocker, bot, dummy_event, dummy_redditor):
    dummy_event.start_date = datetime(2100, 1, 1)
    mocker.patch.object(bot.store, 'get', return_value=dummy_event)
    with pytest.raises(NotStartedEvent):
        await bot.reserve_claim('test', dummy_redditor)

@pytest.mark.asyncio
async def test_reserve_claim_event_expired(mocker, bot, dummy_event, dummy_redditor):
    dummy_event.expiry_date = datetime(1969, 1, 1)
    mocker.patch.object(bot.store, 'get', return_value=dummy_event)
    with pytest.raises(ExpiredEvent):
        await bot.reserve_claim('test', dummy_redditor)

@pytest.mark.asyncio
async def test_reserve_claim_existing_claim(mocker, bot, dummy_event, dummy_redditor, dummy_claim_reserved):
    mocker.patch.object(bot.store, 'get', return_value=dummy_event)
    mocker.patch.object(bot.store, 'get_filter', return_value=dummy_claim_reserved)
    
    claim = await bot.reserve_claim('test', dummy_redditor)
    assert claim == dummy_claim_reserved
    assert claim.reserved

@pytest.mark.asyncio
async def test_reserve_claim_insufficient_karma(mocker, bot, dummy_event, dummy_redditor):
    dummy_redditor.comment_karma = 0
    dummy_redditor.link_karma = 0
    dummy_event.minimum_karma = 1
    mocker.patch.object(bot.store, 'get', return_value=dummy_event)
    mocker.patch.object(bot.store, 'get_filter', return_value=None)
    with pytest.raises(InsufficientKarma):
        await bot.reserve_claim('test', dummy_redditor)

@pytest.mark.asyncio
async def test_reserve_claim_insufficient_age(mocker, bot, dummy_event, dummy_redditor):
    dummy_redditor.created_utc = datetime.utcnow().timestamp()
    dummy_event.minimum_age = 1
    mocker.patch.object(bot.store, 'get', return_value=dummy_event)
    mocker.patch.object(bot.store, 'get_filter', return_value=None)
    with pytest.raises(InsufficientAccountAge):
        await bot.reserve_claim('test', dummy_redditor)