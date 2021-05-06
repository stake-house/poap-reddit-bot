import pytest
from poapbot.models import Event
from datetime import datetime

@pytest.fixture
def dummy_event():
    return Event(id='test', name='test', code='test', description="", expiry_date=datetime(2030, 1, 1))