import json

from .base import BasePermission
from .helpers import identify_database
from .serializers import DateTimeDecoder, DateTimeEncoder


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
