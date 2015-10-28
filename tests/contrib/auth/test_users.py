import mock
import pytest

from librarian_core.contrib.auth import users as mod


def test_authenticated_only():
    instance = mock.Mock()
    instance.is_authenticated = False
    fn = mock.Mock()
    fn.__name__ = 'somefn'
    fn.return_value = 'test'
    decorated = mod.authenticated_only(fn)
    assert decorated(instance) is None
    assert not fn.called

    instance.is_authenticated = True
    assert decorated(instance, 1, 2) == 'test'
    fn.assert_called_once_with(instance, 1, 2)


@mock.patch.object(mod, 'Options')
@mock.patch.object(mod.Group, 'from_name')
def test___init__(from_name, Options):
    db = mock.Mock()
    user = mod.User(username='username',
                    password='password',
                    reset_token='reset_token',
                    created='created',
                    options='options',
                    groups='a,b,c',
                    db=db)
    Options.assert_called_once_with('options', onchange=user.save)
    from_name.assert_has_calls([mock.call('a', db=db),
                                mock.call('b', db=db),
                                mock.call('c', db=db)])
    assert user.username == 'username'
    assert user.password == 'password'
    assert user.reset_token == 'reset_token'
    assert user.created == 'created'
    assert user.options == Options.return_value
    assert user.groups == [from_name.return_value] * 3
    assert user.db == db


def test_is_authenticated():
    db = mock.Mock()
    user = mod.User(db=db)
    assert user.is_authenticated is False
    user = mod.User(username='test', db=db)
    assert user.is_authenticated is True


def test_is_superuser():
    db = mock.Mock()
    group1 = mock.Mock()
    group1.has_superpowers = False
    group2 = mock.Mock()
    group2.has_superpowers = False
    supergroup = mock.Mock()
    supergroup.has_superpowers = True

    user = mod.User(db=db)
    user.groups = [group1, group2]
    assert user.is_superuser is False

    user.groups = [group1, supergroup, group2]
    assert user.is_superuser is True


@mock.patch.object(mod, 'request')
def test_logout(request):
    db = mock.Mock()
    user = mod.User(username='test', db=db)
    user.logout()
    request.session.delete.assert_called_once_with()
    request.session.delete.return_value.reset.assert_called_once_with()
    assert isinstance(request.user, mod.User)
    assert request.user.is_authenticated is False


@mock.patch.object(mod, 'Options')
def test_save(Options):
    db = mock.Mock()
    user = mod.User(username='test', db=db)
    group1 = mock.Mock()
    group1.name = 'grp1'
    group2 = mock.Mock()
    group2.name = 'grp2'
    user.groups = [group1, group2]
    user.options = Options()

    user.save()

    db.Replace.assert_called_once_with('users', cols=('username',
                                                      'password',
                                                      'reset_token',
                                                      'created',
                                                      'options',
                                                      'groups'))
    db.query.assert_called_once_with(db.Replace.return_value,
                                     username=user.username,
                                     password=user.password,
                                     reset_token=user.reset_token,
                                     created=user.created,
                                     options=user.options.to_json.return_value,
                                     groups='grp1,grp2')


@mock.patch.object(mod, 'Options')
@mock.patch.object(mod, 'json')
def test_to_json(json, Options):
    db = mock.Mock()
    user = mod.User(username='test', db=db)
    group1 = mock.Mock()
    group1.name = 'grp1'
    group2 = mock.Mock()
    group2.name = 'grp2'
    user.groups = [group1, group2]
    user.options = Options()

    assert user.to_json() == json.dumps.return_value

    data = dict(username=user.username,
                password=user.password,
                reset_token=user.reset_token,
                created=user.created,
                options=user.options.to_native.return_value,
                groups='grp1,grp2')
    json.dumps.assert_called_once_with(data, cls=mod.DateTimeEncoder)


@mock.patch.object(mod.User, '__init__')
@mock.patch.object(mod, 'json')
def test_from_json(json, init):
    data = '{"a": 1, "b": 2}'
    json.loads.return_value = {'a': 1, 'b': 2}
    init.return_value = None
    mod.User.from_json(data)
    json.loads.assert_called_once_with(data, cls=mod.DateTimeDecoder)
    init.assert_called_once_with(**json.loads.return_value)


@mock.patch.object(mod.User, '__init__')
def test_from_username(init):
    init.return_value = None
    db = mock.Mock()
    db.result = {'a': 1, 'b': 2}

    mod.User.from_username('test', db=db)

    db.Select.assert_called_once_with(sets='users', where='username = ?')
    db.query.assert_called_once_with(db.Select.return_value, 'test')
    init.assert_called_once_with(**db.result)


@mock.patch.object(mod.User, '__init__')
@mock.patch.object(mod, 'hashlib')
def test_from_reset_token(hashlib, init):
    hashed_token = hashlib.sha1.return_value.hexdigest.return_value
    init.return_value = None
    db = mock.Mock()
    db.result = {'a': 1, 'b': 2}

    mod.User.from_reset_token('token', db=db)

    db.Select.assert_called_once_with(sets='users', where='reset_token = ?')
    db.query.assert_called_once_with(db.Select.return_value, hashed_token)
    init.assert_called_once_with(**db.result)


@mock.patch.object(mod, 'utcnow')
@mock.patch.object(mod.User, '__init__')
@mock.patch.object(mod.User, 'save')
@mock.patch.object(mod.User, 'encrypt_password')
@mock.patch.object(mod.User, 'generate_reset_token')
def test_create(generate_reset_token, encrypt_password, save, init, utcnow):
    init.return_value = None
    hashed_token = 'fe1e872688cd46b69bd5317c14965c39ba250848'
    db = mock.Mock()
    mod.User.create('username', 'password', reset_token='that token', db=db)
    data = {'username': 'username',
            'password': encrypt_password.return_value,
            'reset_token': hashed_token,
            'created': utcnow.return_value,
            'options': {},
            'groups': ''}
    assert not generate_reset_token.called
    encrypt_password.assert_called_once_with('password')
    init.assert_called_once_with(db=db, **data)
    save.assert_called_once_with()


@mock.patch.object(mod.User, 'save')
@mock.patch.object(mod.User, '__init__')
@mock.patch.object(mod.User, 'generate_reset_token')
def test_create_generate_reset_token(generate_reset_token, init, save):
    generate_reset_token.return_value = 'this token'
    hashed_token = '1afe6afa4c007093d7f3700c66e3fd51449fb137'

    def check_kwargs(*args, **kwargs):
        assert kwargs['reset_token'] == hashed_token

    init.return_value = None
    init.side_effect = check_kwargs
    db = mock.Mock()
    mod.User.create('username', 'password', db=db)
    generate_reset_token.assert_called_once_with()


@mock.patch.object(mod.User, 'save')
@mock.patch.object(mod.User, '__init__')
def test_create_superuser(init, save):
    def check_kwargs(*args, **kwargs):
        assert kwargs['groups'] == 'superuser'

    init.return_value = None
    init.side_effect = check_kwargs
    db = mock.Mock()
    mod.User.create('username1234', 'password', is_superuser=True, db=db)


@pytest.mark.parametrize('credentials', [
    ('', 'password'),
    ('a ', 'password'),
    (' a', 'password'),
    (' ', 'password'),
    ('\n', 'password'),
    ('toolonguserna', 'password'),
    ('username', ''),
])
def test_create_invalid_credentials(credentials):
    (username, password) = credentials
    db = mock.Mock()
    with pytest.raises(mod.InvalidUserCredentials):
        mod.User.create(username, password, db=db)


def test_create_invalid_credentials():
    db = mock.Mock()
    with pytest.raises(mod.InvalidUserCredentials):
        mod.User.create('', 'password', db=db)
        mod.User.create('username', '', db=db)


@mock.patch.object(mod.User, 'from_username')
@mock.patch.object(mod, 'request')
def test_login_invalid_user(request, from_username):
    db = mock.Mock()
    from_username.return_value = None
    assert mod.User.login('name', 'pass', db=db) is False
    assert request.user != from_username.return_value


@mock.patch.object(mod.User, 'is_valid_password')
@mock.patch.object(mod.User, 'from_username')
@mock.patch.object(mod, 'request')
def test_login_invalid_password(request, from_username, is_valid_password):
    db = mock.Mock()
    is_valid_password.return_value = False
    assert mod.User.login('name', 'pass', db=db) is False
    assert request.user != from_username.return_value


@mock.patch.object(mod.User, 'is_valid_password')
@mock.patch.object(mod.User, 'from_username')
@mock.patch.object(mod, 'request')
def test_login_success(request, from_username, is_valid_password):
    db = mock.Mock()
    assert mod.User.login('name', 'pass', db=db) == from_username.return_value
    assert request.user == from_username.return_value
    request.session.rotate.assert_called_once_with()


@mock.patch.object(mod.User, 'encrypt_password')
def test_set_password(encrypt_password):
    db = mock.Mock()
    mod.User.set_password('username', 'password', db=db)
    encrypt_password.assert_called_once_with('password')
    db.Update.assert_called_once_with('users',
                                      password=':password',
                                      where='username = :username')
    db.query.assert_called_once_with(db.Update.return_value,
                                     username='username',
                                     password=encrypt_password.return_value)


@mock.patch.object(mod, 'pbkdf2')
def test_encrypt_password(pbkdf2):
    assert mod.User.encrypt_password('password') == pbkdf2.crypt.return_value
    pbkdf2.crypt.assert_called_once_with('password')


@mock.patch.object(mod, 'pbkdf2')
def test_is_valid_password(pbkdf2):
    pbkdf2.crypt.return_value = 'encrypted'
    assert mod.User.is_valid_password('password', 'encrypted') is True
    pbkdf2.crypt.assert_called_once_with('password', 'encrypted')


@mock.patch.object(mod, 'generate_random_key')
def test_generate_reset_token(generate_random_key):
    assert mod.User.generate_reset_token() == generate_random_key.return_value
    generate_random_key.assert_called_once_with(letters=False,
                                                digits=True,
                                                punctuation=False,
                                                length=6)
