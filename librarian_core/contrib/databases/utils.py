import datetime

import pytz


def utcnow():
    """Return a timezone aware datetime object in UTC."""
    return datetime.datetime.now(tz=pytz.utc)
