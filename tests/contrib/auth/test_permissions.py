import mock
import pytest

from librarian_core.contrib.auth import permissions as mod


@pytest.fixture
def dyn_perm_cls():
    class CustomDynamicPermission(mod.BaseDynamicPermission):
        name = 'dynamo'
    return CustomDynamicPermission


class TestBaseDynamicPermission(object):

    @mock.patch.object(mod.BaseDynamicPermission, '_load')
    def test___init__(self, _load, dyn_perm_cls):
        db = mock.Mock()
        bdp = dyn_perm_cls('id', db=db)
        assert bdp.identifier == 'id'
        assert bdp.db == db
        assert bdp.data == _load.return_value
        _load.assert_called_once_with()

    @mock.patch.object(mod, 'json')
    def test__load(self, json, dyn_perm_cls):
        db = mock.Mock()
        bdp = dyn_perm_cls('id', db=db)

        db.Select.assert_called_once_with(
            sets='permissions',
            where='name = :name AND identifier = :identifier'
        )
        db.query.assert_called_once_with(db.Select.return_value,
                                         name='dynamo',
                                         identifier='id')
        json.load.assert_called_once_with(db.result.data,
                                          cls=mod.DateTimeDecoder)
        assert bdp.data == json.load.return_value
