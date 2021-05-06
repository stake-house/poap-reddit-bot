import pytest
from poapbot.models import Attendee
from datetime import datetime

@pytest.fixture
def dummy_attendee():
    return Attendee(username='dummy_username')