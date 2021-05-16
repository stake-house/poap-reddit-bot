import pytest
from poapbot.db import POAPDatabase

@pytest.fixture(autouse=True)
def db():
    return POAPDatabase()