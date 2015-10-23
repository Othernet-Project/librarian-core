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


class TestACLPermission(object):

    @mock.patch.object(mod.ACLPermission, '_load')
    def test_to_bitmask(self, _load):
        db = mock.Mock()
        acl = mod.ACLPermission('id', db=db)
        fn = mock.Mock()
        fn.__name__ = 'fn'
        unwrapped = acl.to_bitmask.__func__
        decorated = unwrapped(fn)
        bait = range(1, 8) + ['r', 'w', 'x', 'rw', 'rx', 'wx', 'wrx']
        expected = range(1, 8) + [4, 2, 1, 6, 5, 3, 7]
        for (in_perm, out_perm) in zip(bait, expected):
            decorated(acl, 'path', in_perm)
            fn.assert_called_once_with(acl, 'path', out_perm)
            fn.reset_mock()

        for perm in (0, 8, None, 'a', 'TT'):
            with pytest.raises(ValueError):
                decorated(acl, 'path', perm)
            assert not fn.called

    @mock.patch.object(mod.ACLPermission, 'save')
    @mock.patch.object(mod.ACLPermission, '_load')
    def test_grant_already_granted(self, _load, save):
        db = mock.Mock()
        acl = mod.ACLPermission('id', db=db)
        acl.data = dict()
        acl.data['path'] = 4
        acl.grant('path', 1)
        assert acl.data['path'] == 5
        save.assert_called_once_with()

        acl.grant('path', 1)
        assert acl.data['path'] == 5

        acl.grant('path', 2)
        assert acl.data['path'] == 7

        acl.grant('path', 3)
        assert acl.data['path'] == 7

        acl.grant('path', 6)
        assert acl.data['path'] == 7

    @mock.patch.object(mod.ACLPermission, 'save')
    @mock.patch.object(mod.ACLPermission, '_load')
    def test_grant_adds_new(self, _load, save):
        db = mock.Mock()
        acl = mod.ACLPermission('id', db=db)
        acl.data = dict()
        acl.grant('path', 4)
        assert acl.data['path'] == 4
        save.assert_called_once_with()

    @mock.patch.object(mod.ACLPermission, 'save')
    @mock.patch.object(mod.ACLPermission, '_load')
    def test_revoke_to_no_permission(self, _load, save):
        db = mock.Mock()
        acl = mod.ACLPermission('id', db=db)
        acl.data = dict()
        acl.revoke('path', 4)
        assert acl.data == dict()
        save.assert_called_once_with()

    @mock.patch.object(mod.ACLPermission, 'save')
    @mock.patch.object(mod.ACLPermission, '_load')
    def test_revoke_to_remaining_permissions(self, _load, save):
        db = mock.Mock()
        acl = mod.ACLPermission('id', db=db)
        acl.data = dict(path=7)
        acl.revoke('path', 4)
        assert acl.data == dict(path=3)
        save.assert_called_once_with()

        acl.revoke('path', 4)
        assert acl.data == dict(path=3)

        acl.revoke('path', 1)
        assert acl.data == dict(path=2)

        acl.revoke('path', 2)
        assert acl.data == dict()

    @mock.patch.object(mod.ACLPermission, 'save')
    @mock.patch.object(mod.ACLPermission, '_load')
    def test_clear(self, _load, save):
        db = mock.Mock()
        acl = mod.ACLPermission('id', db=db)
        acl.data = dict(path=7)
        acl.clear()
        assert acl.data == dict()
        save.assert_called_once_with()

    @mock.patch.object(mod.ACLPermission, '_load')
    def test_is_granted(self, _load):
        db = mock.Mock()
        acl = mod.ACLPermission('id', db=db)
        acl.data = dict(path=5)
        assert acl.is_granted('path', 1) is True
        assert acl.is_granted('path', 4) is True
        assert acl.is_granted('path', 5) is True
        assert acl.is_granted('path', 2) is False
        assert acl.is_granted('path', 6) is False
        assert acl.is_granted('path', 3) is False
        assert acl.is_granted('path', 7) is False
        assert acl.is_granted('path', 'r') is True
        assert acl.is_granted('path', 'x') is True
        assert acl.is_granted('path', 'rx') is True
        assert acl.is_granted('path', 'xr') is True
        assert acl.is_granted('path', 'rw') is False
        assert acl.is_granted('path', 'wr') is False
        assert acl.is_granted('path', 'wx') is False
        assert acl.is_granted('path', 'w') is False
        assert acl.is_granted('invalid', 'w') is False
