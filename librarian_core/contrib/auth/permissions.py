import functools
import json

from ...utils import is_string
from ..databases.serializers import DateTimeDecoder, DateTimeEncoder

from .base import BasePermission
from .helpers import identify_database


class BaseDynamicPermission(BasePermission):

    @identify_database
    def __init__(self, identifier, db):
        super(BaseDynamicPermission, self).__init__()
        self.db = db
        self.identifier = identifier
        self.data = self._load()

    def _load(self):
        q = self.db.Select(sets='permissions',
                           where='name = :name AND identifier = :identifier')
        self.db.query(q, name=self.name, identifier=self.identifier)
        result = self.db.result
        if result:
            return json.loads(result.data, cls=DateTimeDecoder)
        return {}

    def save(self):
        q = self.db.Replace('permissions',
                            name=':name',
                            identifier=':identifier',
                            data=':data',
                            where='name = :name AND identifier = :identifier')
        data = json.dumps(self.data, cls=DateTimeEncoder)
        self.db.query(q, name=self.name, identifier=self.identifier, data=data)


class ACLPermission(BaseDynamicPermission):
    name = 'acl'

    NO_PERMISSION = 0
    READ = 4
    WRITE = 2
    EXECUTE = 1
    ALIASES = {
        'r': READ,
        'w': WRITE,
        'x': EXECUTE,
        READ: READ,
        WRITE: WRITE,
        EXECUTE: EXECUTE
    }
    VALID_BITMASKS = range(1, 8)

    def convert_permission(func):
        @functools.wraps(func)
        def wrapper(self, path, permission):
            if is_string(permission):
                try:
                    bitmask = sum([self.ALIASES[p] for p in list(permission)])
                except KeyError:
                    msg = "Invalid permission: {0}".format(permission)
                    raise ValueError(msg)
            else:
                bitmask = permission

            if bitmask not in self.VALID_BITMASKS:
                msg = "Invalid permission: {0}".format(permission)
                raise ValueError(msg)

            return func(self, path, bitmask)
        return wrapper

    @convert_permission
    def grant(self, path, permission):
        existing = self.data.get(path, self.NO_PERMISSION)
        self.data[path] = existing | permission
        self.save()

    @convert_permission
    def revoke(self, path, permission):
        existing = self.data.get(path, self.NO_PERMISSION)
        permission = existing & ~permission
        if permission == self.NO_PERMISSION:
            # when having no permission, we can freely just remove the whole
            # path as not having a path at all also means having no permissions
            # whatsoever
            self.data.pop(path, None)
        else:
            self.data[path] = permission

        self.save()

    def clear(self):
        self.data = {}
        self.save()

    @convert_permission
    def is_granted(self, path, permission):
        existing = self.data.get(path, self.NO_PERMISSION)
        return existing & permission == permission
