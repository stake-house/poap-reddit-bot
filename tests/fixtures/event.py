import pytest
from poapbot.models import Event
from datetime import datetime

@pytest.fixture
def dummy_event():
    return Event(id='test', name='test', code='test', description="", start_date=datetime(1970, 1, 1), expiry_date=datetime(2100, 1, 1))