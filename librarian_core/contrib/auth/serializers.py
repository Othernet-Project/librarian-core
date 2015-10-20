import datetime
import json
import re

import dateutil.parser

from ...utils import is_string


NUMERIC_RE = re.compile(r'^[\d\.]+$')


class DateTimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        return super(DateTimeEncoder, self).default(obj)


class DateTimeDecoder(json.JSONDecoder):

    def __init__(self, *args, **kargs):
        super(DateTimeDecoder, self).__init__(object_hook=self.object_hook,
                                              *args,
                                              **kargs)

    def object_hook(self, obj):
        for key, value in obj.items():
            if is_string(value) and not NUMERIC_RE.match(value) and value:
                try:
                    obj[key] = dateutil.parser.parse(value)
                except (ValueError, TypeError):
                    pass
        return obj
