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
