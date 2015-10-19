from .contrib.databases.utils import utcnow  # NOQA


def is_string(obj):
    try:
        return isinstance(obj, basestring)
    except NameError:
        return isinstance(obj, str)
