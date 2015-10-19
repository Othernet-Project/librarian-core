import datetime

import mock
import pytest

from librarian_core.contrib.sessions import sessions as mod


@mock.patch.object(mod.Session, '_load')
def test___init__(_load):
    data = 'data'
    sess = mod.Session('id', data, 'expires')
    sess._load.assert_called_once_with(data)
    assert sess.data == _load.return_value


def test__load():
    sess = mod.Session('id', {}, 'expires')

    assert sess._load('{"a": 1}') == {"a": 1}
    assert sess._load({"a": 1}) == {"a": 1}
    assert sess._load(None) == {}
    assert sess._load(111) == {}


def test__dump():
    sess = mod.Session('id', {'a': 1}, 'expires')
    assert sess._dump() == '{"a": 1}'


@mock.patch.object(mod.Session, '_dump')
@mock.patch.object(mod, 'request')
def test_save(request, _dump):
    sess = mod.Session('id', {'a': 1}, 'expires')
    sess.modified = True
    assert sess.save() is sess

    db = request.db.sessions
    db.Replace.assert_called_once_with('sessions',
                                       cols=['session_id', 'data', 'expires'])
    db.query.assert_called_once_with(db.Replace.return_value,
                                     session_id=sess.id,
                                     data=_dump.return_value,
                                     expires=sess.expires)


@mock.patch.object(mod, 'request')
def test_delete(request):
    sess = mod.Session('id', {'a': 1}, 'expires')
    assert sess.delete() is sess
    db = request.db.sessions
    db.Delete.assert_called_once_with('sessions', where='session_id = ?')
    db.query.assert_called_once_with(db.Delete.return_value, sess.id)


@mock.patch.object(mod.Session, 'save')
@mock.patch.object(mod.Session, 'generate_session_id')
@mock.patch.object(mod.Session, 'delete')
def test_rotate(delete, generate_session_id, save):
    sess = mod.Session('id', {'a': 1}, 'expires')
    assert sess.rotate() == save.return_value

    delete.assert_called_once_with()
    assert sess.id == generate_session_id.return_value
    save.assert_called_once_with()


@mock.patch.object(mod.Session, 'delete')
def test_expire_not_expired(delete):
    sess = mod.Session('id', {'a': 1}, mod.utcnow() + datetime.timedelta(100))
    assert sess.expire() is sess
    assert not delete.called


@mock.patch.object(mod.Session, 'delete')
def test_expire_expired(delete):
    sess = mod.Session('id', {'a': 1}, mod.utcnow() - datetime.timedelta(100))
    with pytest.raises(mod.SessionExpired):
        sess.expire()

    delete.assert_called_once_with()


@mock.patch.object(mod.Session, 'get_expiry')
@mock.patch.object(mod.Session, 'generate_session_id')
def test_reset(generate_session_id, get_expiry):
    sess = mod.Session('id', {'a': 1}, 'expires')
    assert sess.reset() is sess
    assert sess.id == generate_session_id.return_value
    assert sess.expires == get_expiry.return_value
    assert sess.data == {}


def test___setattr__():
    sess = mod.Session('id', {}, 'expires')
    assert sess.modified is False
    # should still show False
    sess.non_modifiable = 'test'
    assert sess.modified is False
    # should record modification
    sess.data = 'test'
    assert sess.modified is True


@mock.patch.object(mod.Session, 'expire')
@mock.patch.object(mod.Session, '__init__')
@mock.patch.object(mod, 'request')
def test_fetch_success(request, init, expire):
    session_id = 'session_id'
    init.return_value = None
    db = request.db.sessions
    db.result.return_value = dict(a=1, b=2)

    assert mod.Session.fetch(session_id) == expire.return_value

    db.Select.assert_called_once_with(sets='sessions', where='session_id = ?')
    db.query.assert_called_once_with(db.Select.return_value, session_id)
    init.assert_called_once_with(**db.result)
    expire.assert_called_once_with()


@mock.patch.object(mod, 'request')
def test_fetch_invalid(request):
    request.db.sessions.result = None
    with pytest.raises(mod.SessionInvalid):
        mod.Session.fetch('session_id')


@mock.patch.object(mod.Session, 'save')
@mock.patch.object(mod.Session, '__init__')
@mock.patch.object(mod.Session, 'get_expiry')
@mock.patch.object(mod.Session, 'generate_session_id')
def test_create(generate_session_id, get_expiry, init, save):
    init.return_value = None
    mod.Session.create()
    init.assert_called_once_with(generate_session_id.return_value,
                                 {},
                                 get_expiry.return_value,
                                 modified=True)
    save.assert_called_once_with()


@mock.patch.object(mod, 'request')
def test_get_expiry(request):
    request.app.config = {'session.lifetime': 100}
    assert isinstance(mod.Session.get_expiry(), datetime.datetime)
