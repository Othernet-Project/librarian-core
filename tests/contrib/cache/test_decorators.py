import mock

from librarian_core.contrib.cache import cache
from librarian_core.contrib.cache import decorators as mod


@mock.patch.object(mod, 'request')
def test_cached_no_backend(request):
    request.app.supervisor.exts.cache = cache.NoOpCache()
    orig_func = mock.Mock(__name__='orig_func')
    orig_func.return_value = 'data'
    cached_func = mod.cached()(orig_func)

    result = cached_func('test', a=3)
    assert result == 'data'
    orig_func.assert_called_once_with('test', a=3)


@mock.patch.object(cache.BaseCache, 'set')
@mock.patch.object(cache.BaseCache, 'get')
@mock.patch.object(cache.BaseCache, 'parse_prefix')
@mock.patch.object(mod, 'generate_key')
@mock.patch.object(mod, 'request')
def test_cached_found(request, generate_key, parse_prefix, get, setfunc,
                      base_cache):
    request.app.supervisor.exts.cache = base_cache
    orig_func = mock.Mock(__name__='orig_func')
    generate_key.return_value = 'md5_key'
    parse_prefix.return_value = ''
    get.return_value = 'data'
    cached_func = mod.cached()(orig_func)

    result = cached_func('test', a=3)
    assert result == 'data'
    generate_key.assert_called_once_with('orig_func', 'test', a=3)
    get.assert_called_once_with('md5_key')
    assert not setfunc.called


@mock.patch.object(cache.BaseCache, 'set')
@mock.patch.object(cache.BaseCache, 'get')
@mock.patch.object(cache.BaseCache, 'parse_prefix')
@mock.patch.object(mod, 'generate_key')
@mock.patch.object(mod, 'request')
def test_cached_not_found(request, generate_key, parse_prefix, get, setfunc,
                          base_cache):
    request.app.supervisor.exts.cache = base_cache
    orig_func = mock.Mock(__name__='orig_func')
    orig_func.return_value = 'fresh'
    parse_prefix.return_value = ''
    generate_key.return_value = 'md5_key'
    get.return_value = None
    cached_func = mod.cached()(orig_func)

    result = cached_func('test', a=3)
    assert result == 'fresh'
    generate_key.assert_called_once_with('orig_func', 'test', a=3)
    get.assert_called_once_with('md5_key')
    setfunc.assert_called_once_with('md5_key',
                                    'fresh',
                                    timeout=base_cache.default_timeout)


@mock.patch.object(cache.BaseCache, 'set')
@mock.patch.object(cache.BaseCache, 'get')
@mock.patch.object(cache.BaseCache, 'parse_prefix')
@mock.patch.object(mod, 'generate_key')
@mock.patch.object(mod, 'request')
def test_cached_not_found_no_timeout(request, generate_key, parse_prefix, get,
                                     setfunc, base_cache):
    request.app.supervisor.exts.cache = base_cache
    orig_func = mock.Mock(__name__='orig_func')
    orig_func.return_value = 'fresh'
    parse_prefix.return_value = ''
    generate_key.return_value = 'md5_key'
    get.return_value = None
    cached_func = mod.cached(timeout=0)(orig_func)

    cached_func('test', a=3)
    setfunc.assert_called_once_with('md5_key', 'fresh', timeout=0)


@mock.patch.object(cache.BaseCache, 'set')
@mock.patch.object(cache.BaseCache, 'get')
@mock.patch.object(cache.BaseCache, 'parse_prefix')
@mock.patch.object(mod, 'generate_key')
@mock.patch.object(mod, 'request')
def test_cached_not_found_custom_timeout(request, generate_key, parse_prefix,
                                         get, setfunc, base_cache):
    request.app.supervisor.exts.cache = base_cache
    orig_func = mock.Mock(__name__='orig_func')
    orig_func.return_value = 'fresh'
    parse_prefix.return_value = ''
    generate_key.return_value = 'md5_key'
    get.return_value = None
    cached_func = mod.cached(timeout=180)(orig_func)

    cached_func('test', a=3)
    setfunc.assert_called_once_with('md5_key', 'fresh', timeout=180)


@mock.patch.object(cache.BaseCache, 'set')
@mock.patch.object(cache.BaseCache, 'get')
@mock.patch.object(cache.BaseCache, 'parse_prefix')
@mock.patch.object(mod, 'generate_key')
@mock.patch.object(mod, 'request')
def test_cached_not_found_custom_prefix(request, generate_key, parse_prefix,
                                        get, setfunc, base_cache):
    request.app.supervisor.exts.cache = base_cache
    orig_func = mock.Mock(__name__='orig_func')
    orig_func.return_value = 'fresh'
    parse_prefix.return_value = 'test_'
    generate_key.return_value = 'md5_key'
    get.return_value = None
    cached_func = mod.cached(prefix='test_', timeout=180)(orig_func)

    cached_func('test', a=3)
    parse_prefix.assert_called_once_with('test_')
    get.assert_called_once_with('test_md5_key')
    setfunc.assert_called_once_with('test_md5_key', 'fresh', timeout=180)
