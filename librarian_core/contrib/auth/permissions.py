import json

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
        return json.load(self.db.result.data, cls=DateTimeDecoder)

    def save(self):
        q = self.db.Replace('permissions',
                            name=':name',
                            identifier=':identifier',
                            data=':data',
                            where='name = :name AND identifier = :identifier')
        data = json.dumps(self.data, cls=DateTimeEncoder)
        self.db.query(q, name=self.name, identifier=self.identifier, data=data)


class ACLPermission(BaseDynamicPermission):
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

    def grant(self, path, permission):
        existing = self.data.get(path, self.NO_PERMISSION)
        if existing & permission:
            # permission already granted, so just keep as it is
            new_permission = existing
        else:
            # add to existing permission
            new_permission = existing + permission

        self.data[path] = new_permission
        self.save()

    def revoke(self, path, permission):
        existing = self.data.get(path, self.NO_PERMISSION)
        if existing & permission:
            # contains permission so it needs to be revoked
            new_permission = existing - permission
        else:
            # didn't even have that permission, so just retain the existing one
            new_permission = existing

        if new_permission == self.NO_PERMISSION:
            # when having no permission, we can freely just remove the whole
            # path as not having a path at all also means having no permissions
            # whatsoever
            self.data.pop(path, None)
        else:
            self.data[path] = new_permission

        self.save()

    def clear(self):
        self.data = {}
        self.save()

    def is_granted(self, path, permission='r'):
        try:
            permission = self.ALIASES[permission]
        except KeyError:
            msg = "Invalid permission specified: {0}".format(permission)
            raise ValueError(msg)
        else:
            existing = self.data.get(path, self.NO_PERMISSION)
            return existing & permission
