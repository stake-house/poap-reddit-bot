import pytest
from poapbot.db.models import Claim

@pytest.fixture
def dummy_claim(dummy_event):
    return Claim(event=dummy_event, link='test.com')

@pytest.fixture
def dummy_claim_reserved(dummy_event, dummy_attendee):
    return Claim(event=dummy_event, link='test.com', reserved=True, attendee=dummy_attendee)