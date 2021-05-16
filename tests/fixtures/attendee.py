import pytest
from poapbot.db.models import Attendee
from datetime import datetime

@pytest.fixture
def dummy_attendee():
    return Attendee(username='dummy_username')