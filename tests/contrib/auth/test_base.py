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
