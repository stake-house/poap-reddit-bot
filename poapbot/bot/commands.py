import re

CREATE_EVENT_PATTERN = re.compile(r'create_event (?P<id>\w+) (?P<name>\w+) (?P<code>\w+) (?P<start_date>[\w:-]+) (?P<expiry_date>[\w:-]+) (?P<minimum_age>\w+) (?P<minimum_karma>\w+)')
UPDATE_EVENT_PATTERN = re.compile(r'update_event (?P<id>\w+) (?P<name>\w+) (?P<code>\w+) (?P<start_date>[\w:-]+) (?P<expiry_date>[\w:-]+) (?P<minimum_age>\w+) (?P<minimum_karma>\w+)')
CREATE_CLAIMS_PATTERN = re.compile(r'create_claims (?P<event_id>\w+) (?P<codes>(\w+,?)+)')

class Command:
    pass

class CreateEventCommand(Command):

    name = 'create_event'
    pattern = CREATE_EVENT_PATTERN
    example = \
        """'create_event event_id event_name event_code start_date expiry_date minimum_age minimum_karma'\n\n""" \
        """Date strings must be in UTC and ISO8601 formatted, eg. 2021-05-01T00:00:00"""

class UpdateEventCommand(Command):

    name = 'update_event'
    pattern = UPDATE_EVENT_PATTERN
    example = \
        """'update_event event_id event_name event_code start_date expiry_date minimum_age minimum_karma'\n\n""" \
        """Date strings must be in UTC and ISO8601 formatted, eg. 2021-05-01T00:00:00"""

class CreateClaimsCommand(Command):

    name = 'create_claims'
    pattern = CREATE_CLAIMS_PATTERN
    example = """'create_claims event_id code1,code2,code3'"""
