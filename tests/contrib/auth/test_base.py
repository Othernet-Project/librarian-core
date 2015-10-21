import mock
import pytest

from librarian_core.contrib.auth import base as mod


@pytest.fixture
def bad_permission_cls():
    class BadPermission(mod.BasePermission):
        pass
    return BadPermission


@pytest.fixture
def permission():
    class CustomPermission(mod.BasePermission):
        name = 'custom'
    return CustomPermission()


@pytest.fixture
def user_cls():
    class User(mod.BaseUser):
        pass
    return User


class TestBasePermission(object):

    def test_unnamed_permission(self, bad_permission_cls):
        with pytest.raises(ValueError):
            bad_permission_cls()

    def test_is_granted(self, permission):
        assert permission.is_granted() is True

    def test_subclasses(self):
        class ChildPermission(mod.BasePermission):
            pass

        class AnotherPermission(mod.BasePermission):
            pass

        class GrandChildPermission(mod.BasePermission):
            pass

        children = mod.BasePermission.subclasses()
        for expected in (ChildPermission,
                         AnotherPermission,
                         GrandChildPermission):
            assert expected in children

    def test_cast_success(self):
        class SomePermission(mod.BasePermission):
            name = 'some'
        assert mod.BasePermission.cast('some') is SomePermission

    def test_cast_not_found(self):
        with pytest.raises(ValueError):
            mod.BasePermission.cast('never_heard_of')


class TestBaseGroup(object):

    @mock.patch.object(mod, 'BasePermission')
    def test___init__(self, BasePermission):
        group = mod.BaseGroup('name',
                              permissions=('this', 'that'),
                              has_superpowers=True)
        BasePermission.cast.assert_has_calls([mock.call('this'),
                                              mock.call('that')])
        assert group.has_superpowers is True
        assert group.name == 'name'
        assert group.permission_classes == [BasePermission.cast.return_value,
                                            BasePermission.cast.return_value]

    @mock.patch.object(mod, 'BasePermission')
    def test_contains_permission(self, BasePermission):
        group = mod.BaseGroup('name')
        perm1 = mock.Mock()
        perm2 = mock.Mock()
        perm3 = mock.Mock()
        group.permission_classes = [perm1, perm2]
        assert group.contains_permission(perm1) is True
        assert group.contains_permission(perm2) is True
        assert group.contains_permission(perm3) is False

    @mock.patch.object(mod, 'BasePermission')
    def test_add_permission(self, BasePermission):
        group = mod.BaseGroup('name')
        assert group.permission_classes == []
        perm = mock.Mock()
        group.add_permission(perm)
        assert group.permission_classes == [perm]

    @mock.patch.object(mod, 'BasePermission')
    def test_remove_permission(self, BasePermission):
        group = mod.BaseGroup('name')
        perm1 = mock.Mock()
        perm2 = mock.Mock()
        group.permission_classes = [perm1, perm2]
        # try removing existing permission
        group.remove_permission(perm1)
        assert group.permission_classes == [perm2]
        # try removing non-existing permission
        group.remove_permission(perm1)
        assert group.permission_classes == [perm2]

    @mock.patch.object(mod, 'BasePermission')
    def test_permissions(self, BasePermission):
        group = mod.BaseGroup('name')
        perm1 = mock.Mock()
        perm1.name = 'perm1'
        perm2 = mock.Mock()
        perm2.name = 'perm2'
        group.permission_classes = [perm1, perm2]
        assert group.permissions == ['perm1', 'perm2']


class TestBaseUser(object):

    def test_abstract_user_guard(self):
        with pytest.raises(TypeError):
            mod.BaseUser()

    def test___init__(self):
        class User(mod.BaseUser):
            pass

        assert User(None).groups == []
        assert User([1, 2]).groups == [1, 2]

    @mock.patch.object(mod, 'BasePermission')
    def test_has_permission_from_string(self, BasePermission, user_cls):
        user = user_cls([])
        user.has_permission('test')
        BasePermission.cast.assert_called_once_with('test')

    def test_has_permission_superuser(self, user_cls):
        group1 = mock.Mock()
        group1.contains_permission.return_value = False
        group1.has_superpowers = False
        group2 = mock.Mock()
        group2.contains_permission.return_value = False
        group2.has_superpowers = True
        user = user_cls([group1, group2])
        perm_cls = mock.Mock()
        assert user.has_permission(perm_cls) is True

    @mock.patch.object(mod.BaseUser, 'get_permission_kwargs')
    def test_has_permission_granted(self, get_permission_kwargs, user_cls):
        get_permission_kwargs.return_value = dict(identifier='username',
                                                  db=mock.Mock())
        group1 = mock.Mock()
        group1.contains_permission.return_value = False
        group1.has_superpowers = False
        group2 = mock.Mock()
        group2.contains_permission.return_value = True
        group2.has_superpowers = False
        user = user_cls([group1, group2])

        perm_cls = mock.Mock()
        perm_instance = perm_cls.return_value
        perm_instance.is_granted.return_value = True

        assert user.has_permission(perm_cls, 'some_param', 1, a=4) is True
        perm_cls.assert_called_once_with(**get_permission_kwargs.return_value)
        perm_instance.is_granted.assert_called_once_with('some_param', 1, a=4)

    def test_has_permission_no_groups(self, user_cls):
        user = user_cls([])
        perm_cls = mock.Mock()
        assert user.has_permission(perm_cls) is False
