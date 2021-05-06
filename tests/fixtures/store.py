import pytest
from poapbot.store import EventDataStore

@pytest.fixture(autouse=True)
def store():
    return EventDataStore(None)