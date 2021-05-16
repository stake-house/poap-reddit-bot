from typing import List, Dict, Union

class DoesNotExist(Exception):
    """Raised when requested resource does not exist"""

class ConflictError(Exception):
    """Raised when a resource conflict occurs or a constraint is violated"""

class BulkError(Exception):
    """Raised when an error in encountered while processing bulk insert"""
    def __init__(self, errors: List[Dict[Union[int,str], str]]):
        self.errors = errors