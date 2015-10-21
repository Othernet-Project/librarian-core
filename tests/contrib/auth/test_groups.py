import mock
import pytest

from librarian_core.contrib.auth import base
from librarian_core.contrib.auth import groups as mod


@mock.patch.object(mod.Group, '__init__')
def test_from_name_found(init):
    init.return_value = None
    db = mock.Mock()
    db.result = {'name': 'group name', 'permissions': 'a,b,c'}

    mod.Group.from_name('group name', db=db)

    db.Select.assert_called_once_with(sets='groups', where='name = :name')
    db.query(db.Select.return_value, name='group name')
    init.assert_called_once_with(name='group name',
                                 permissions=['a', 'b', 'c'],
                                 db=db)


def test_from_name_not_found():
    db = mock.Mock()
    db.result = None
    with pytest.raises(mod.GroupNotFound):
        mod.Group.from_name('group name', db=db)


@mock.patch.object(base.BasePermission, 'cast')
def test_save(cast):
    db = mock.Mock()
    group = mod.Group(db=db, name='group name')
    group.save()
    db.Replace.assert_called_once_with('groups',
                                       name=':name',
                                       permissions=':permissions',
                                       has_superpowers=':has_superpowers',
                                       where='name = :name')
    db.query.assert_called_once_with(db.Replace.return_value,
                                     name=group.name,
                                     permissions=group.permissions,
                                     has_superpowers=group.has_superpowers)
