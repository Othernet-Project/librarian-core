import datetime

import pytz


def utcnow():
    """Return a timezone aware datetime object in UTC."""
    return datetime.datetime.now(tz=pytz.utc)


def from_csv(raw_value):
    return [val.strip() for val in (raw_value or '').split(',') if val]


def to_csv(values):
    return ','.join(values)


def row_to_dict(row):
    return dict((key, row[key]) for key in row.keys()) if row else {}
