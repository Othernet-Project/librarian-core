import mock
import pytest

from librarian_core import exts as mod


class TestPlaceholder(object):

    def test___getattr__(self):
        container = mock.Mock()
        placeholder = mod.Placeholder('extname', 'nested', container, 1)
        cloned = placeholder.some_attr
        assert isinstance(cloned, mod.Placeholder)
        assert cloned._Placeholder__name == 'extname'
        assert cloned._Placeholder__attrpath == 'nested.some_attr'
        assert cloned._Placeholder__parent is container
        assert cloned._Placeholder__onfail == 1

    def test___call___onfail_returns(self):
        placeholder = mod.Placeholder('extname', '', mock.Mock(), 1)
        assert placeholder() == 1

    def test___call___onfail_raises(self):
        class CustomError(Exception):
            pass

        exc = CustomError()
        placeholder = mod.Placeholder('extname', '', mock.Mock(), exc)
        with pytest.raises(CustomError):
            placeholder()

    def test___call___stores_params(self):
        container = mock.Mock()
        placeholder = mod.Placeholder('extname', '', container, mod.Nothing)
        ret = placeholder(1, 2, a='b')
        assert ret is placeholder
        container.store_call.assert_called_once_with('extname',
                                                     '',
                                                     (1, 2),
                                                     dict(a='b'))


class TestExtContainer(object):

    def test___get_extension_found(self):
        extension = mock.Mock()
        ec = mod.ExtContainer()
        ec._extensions['test'] = extension
        assert ec._ExtContainer__get_extension('test') is extension

    def test___get_extension_not_found(self):
        ec = mod.ExtContainer()
        ph = ec.missing
        assert isinstance(ph, mod.Placeholder)
        assert ph._Placeholder__name == 'missing'
        assert ph._Placeholder__attrpath == ''
        assert ph._Placeholder__parent is ec
        assert ph._Placeholder__onfail == mod.Nothing

    def test___install_extension_already_exists(self):
        ec = mod.ExtContainer()
        ec._extensions['test'] = 1
        with pytest.raises(mod.ExtensionAlreadyExists):
            ec._ExtContainer__install_extension('test', 2)

    def test___install_extension_name_unavailable(self):
        ec = mod.ExtContainer()
        with pytest.raises(mod.ExtensionNameUnavailable):
            ec._ExtContainer__install_extension('is_installed', 2)

    @mock.patch.object(mod.ExtContainer, '_ExtContainer__replay_calls')
    def test___install_extension_success(self, __replay_calls):
        ext = mock.Mock()
        ec = mod.ExtContainer()
        ec._ExtContainer__install_extension('test', ext)
        assert ec._extensions['test'] is ext
        __replay_calls.assert_called_once_with('test', ext)

    def test___invoke_no_attrs(self):
        ext = mock.Mock()
        ec = mod.ExtContainer()
        ec._ExtContainer__invoke(ext, '', (1, 2), dict(a=3))
        ext.assert_called_once_with(1, 2, a=3)

    def test___invoke_with_attrs(self):
        ext = mock.Mock()
        ext.nested.method = mock.Mock()
        ec = mod.ExtContainer()
        ec._ExtContainer__invoke(ext, 'nested.method', (1, 2), dict(a=3))
        ext.nested.method.assert_called_once_with(1, 2, a=3)

    @mock.patch.object(mod.logging, 'error')
    def test___invoke_attr_not_found(self, error):
        ext = mock.Mock(spec=['valid_method'])
        ec = mod.ExtContainer()

        with pytest.raises(AttributeError):
            ext.missing_method

        ec._ExtContainer__invoke(ext, 'missing_method', (1, 2), dict(a=3))
        assert error.called

    @mock.patch.object(mod.ExtContainer, '_ExtContainer__invoke')
    def test___replay_calls_found(self, __invoke):
        ec = mod.ExtContainer()
        call1 = ('method_a', (1, 2), dict(a=3))
        call2 = ('nested.method_b', (3, 4), dict(b=4))
        ec._calls['extname'] = [call1, call2]
        ext = mock.Mock()
        ec._ExtContainer__replay_calls('extname', ext)
        __invoke.assert_has_calls([mock.call(ext, *call1),
                                   mock.call(ext, *call2)])

    @mock.patch.object(mod.ExtContainer, '_ExtContainer__invoke')
    def test___replay_calls_cleans_up_properly(self, __invoke):
        ec = mod.ExtContainer()
        call1 = ('method_a', (1, 2), dict(a=3))
        call2 = ('nested.method_b', (3, 4), dict(b=4))
        ec._calls['extname'] = [call1]
        ec._calls['another'] = [call2]
        ext = mock.Mock()
        ec._ExtContainer__replay_calls('extname', ext)
        assert 'extname' not in ec._calls
        assert 'another' in ec._calls

    @mock.patch.object(mod.ExtContainer, '_ExtContainer__invoke')
    def test___replay_calls_not_found(self, __invoke):
        ec = mod.ExtContainer()
        ext = mock.Mock()
        ec._ExtContainer__replay_calls('missing', ext)
        assert not __invoke.called

    @mock.patch.object(mod.ExtContainer, '_ExtContainer__install_extension')
    def test___setattr___member(self, __install_extension):
        ec = mod.ExtContainer()
        assert ec._onfail == mod.Nothing
        ec._onfail = 'test'
        assert ec._onfail == 'test'
        assert not __install_extension.called

    @mock.patch.object(mod.ExtContainer, '_ExtContainer__install_extension')
    def test___setattr___nonmember(self, __install_extension):
        ec = mod.ExtContainer()
        ext = mock.Mock()
        ec.test = ext
        assert 'test' not in dir(ec)
        __install_extension.assert_called_once_with('test', ext)

    @mock.patch.object(mod.ExtContainer, '_ExtContainer__install_extension')
    def test___setitem__(self, __install_extension):
        ec = mod.ExtContainer()
        ext = mock.Mock()
        ec['test'] = ext
        assert 'test' not in dir(ec)
        __install_extension.assert_called_once_with('test', ext)

    @mock.patch.object(mod.ExtContainer, '_ExtContainer__get_extension')
    def test___getattr__(self, __get_extension):
        ec = mod.ExtContainer()
        assert ec.extname == __get_extension.return_value
        __get_extension.assert_called_once_with('extname')

    @mock.patch.object(mod.ExtContainer, '_ExtContainer__get_extension')
    def test___getitem__(self, __get_extension):
        ec = mod.ExtContainer()
        assert ec['extname'] == __get_extension.return_value
        __get_extension.assert_called_once_with('extname')

    def test___call__(self):
        ec = mod.ExtContainer()
        ec._extensions['test'] = 1
        ec._calls['test'] = [(1, 2, 3)]
        second = ec(onfail='test')
        assert second._onfail == 'test'
        assert second._extensions == ec._extensions
        assert second._calls == ec._calls
        assert second._ignore == ec._ignore

    def test_store_call(self):
        ec = mod.ExtContainer()
        ec.store_call('extname', 'method', (1, 2), dict(a=3))
        assert len(ec._calls) == 1
        assert ec._calls == {'extname': [('method', (1, 2), dict(a=3))]}

    def test_store_call_ignore(self):
        ec = mod.ExtContainer()
        ec._ignore = ['extname']
        ec.store_call('extname', 'method', (1, 2), dict(a=3))
        assert len(ec._calls) == 0

    def test_is_installed(self):
        ec = mod.ExtContainer()
        ec['valid'] = 1
        assert ec.is_installed('valid')
        assert not ec.is_installed('missing')

    def test_flush_all(self):
        ec = mod.ExtContainer()
        ec._calls['ext1'] = [1, 2]
        ec._calls['ext2'] = [4, 5]
        ec.flush()
        assert len(ec._calls) == 0

    def test_flush_specific(self):
        ec = mod.ExtContainer()
        ec._calls['ext1'] = [1, 2]
        ec._calls['ext2'] = [4, 5]
        ec._calls['ext3'] = [7, 8]
        ec.flush('ext1', 'ext3')
        assert len(ec._calls) == 1
        assert 'ext1' not in ec._calls
        assert 'ext3' not in ec._calls
        assert ec._calls['ext2'] == [4, 5]

    def test_ignore_calls_from(self):
        ec = mod.ExtContainer()
        assert ec._ignore == []
        ec.ignore_calls_from('a', 'b')
        assert ec._ignore == ['a', 'b']


def test_integration_access_extension():
    test_ext = mock.Mock()
    ec = mod.ExtContainer()
    ec.important = test_ext
    ec.important(1, 2)
    test_ext.assert_called_once_with(1, 2)
    try:
        ec.not_installed('cache')
    except Exception:
        pytest.fail("Should not care whether it exists or not.")


def test_integration_onfail_of_missing_ext():
    ec = mod.ExtContainer()
    result = ec(onfail='return this').missing_ext.method(a=1)
    assert result == 'return this'

    class CustomError(Exception):
        pass

    exc = CustomError()
    with pytest.raises(CustomError):
        ec(onfail=exc).missing()


def test_integration_replay_calls():
    ext = mock.Mock()
    ec = mod.ExtContainer()
    ec.not_yet_here('initializing', kw=42)
    ec.not_yet_here.method1(1, 2, a=4)
    ec.not_yet_here.nested.method2(5, 7, g=9)

    ec.not_yet_here = ext

    ext.assert_called_once_with('initializing', kw=42)
    ext.method1.assert_called_once_with(1, 2, a=4)
    ext.nested.method2.assert_called_once_with(5, 7, g=9)
