import json

from .base import BasePermission
from .helpers import identify_database
from .serializers import DateTimeDecoder


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
