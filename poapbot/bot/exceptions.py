from ..models import Event
from asyncpraw.models import Redditor

class ExpiredEvent(Exception):
    """Raised when trying to claim from an expired event"""
    def __init__(self, event: Event):
        self.event = event

class NoClaimsAvailable(Exception):
    """Raised when trying to claim from an event with no more available claims"""
    def __init__(self, event: Event):
        self.event = event

class InvalidCode(Exception):
    """Raised when provided code is invalid, eg. no event with that code"""
    pass

class InsufficientKarma(Exception):
    """Raised when requestor has insufficient karma"""
    def __init__(self, event: Event):
        self.event = event

class InsufficientAccountAge(Exception):
    """Raised when requestor has insufficient account age"""
    def __init__(self, event: Event):
        self.event = event