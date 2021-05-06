import pytest

class DummyRedditor:

    name = 'dummy_username'
    fullname = 'dummy_username'
    comment_karma = 0
    link_karma = 0
    created_utc = 0

    async def load(self):
        pass

@pytest.fixture
def dummy_redditor():
    return DummyRedditor()