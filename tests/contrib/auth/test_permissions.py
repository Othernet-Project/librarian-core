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
        json.loads.assert_called_once_with(db.result.data,
                                           cls=mod.DateTimeDecoder)
        assert bdp.data == json.loads.return_value

    @mock.patch.object(mod, 'json')
    def test__load_no_data(self, json, dyn_perm_cls):
        db = mock.Mock()
        db.result = None
        bdp = dyn_perm_cls('id', db=db)
        assert not json.loads.called
        assert bdp.data == {}

    @mock.patch.object(mod.BaseDynamicPermission, '_load')
    @mock.patch.object(mod, 'json')
    def test_save(self, json, _load, dyn_perm_cls):
        db = mock.Mock()
        bdp = dyn_perm_cls('id', db=db)
        bdp.data = {'test': 1}
        bdp.save()

        db.Replace.assert_called_once_with(
            'permissions',
            name=':name',
            identifier=':identifier',
            data=':data',
            where='name = :name AND identifier = :identifier'
        )
        json.dumps.assert_called_once_with(bdp.data, cls=mod.DateTimeEncoder)
        db.query.assert_called_once_with(db.Replace.return_value,
                                         name=bdp.name,
                                         identifier=bdp.identifier,
                                         data=json.dumps.return_value)
