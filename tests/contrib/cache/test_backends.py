# -*- coding: utf-8 -*-
import sys
import time
try:
    import __builtin__ as builtins
except ImportError:
    import builtins

import mock
import pytest

from librarian_core.contrib.cache import backends as mod


@pytest.fixture(params=['pylibmc', 'memcache'])
def mc_cache(request):
    def import_mock(name, *args):
        if request.param != name:
            raise ImportError()

        client = mock.Mock()
        client.name = request.param

        client_lib = mock.Mock()
        client_lib.Client.return_value = client

        return client_lib

    with mock.patch.object(builtins, '__import__', side_effect=import_mock):
        instance = mod.MemcachedCache(['127.0.0.1:11211'])
        assert instance._cache.name == request.param
        return instance


class TestBaseCache(object):

    def test_get_expiry(self, base_cache):
        assert base_cache.get_expiry(60) > time.time()
        assert base_cache.get_expiry(None) == 0
        assert base_cache.get_expiry(0) == 0

    def test_has_expired(self, base_cache):
        assert not base_cache.has_expired(0)
        assert not base_cache.has_expired(None)
        assert not base_cache.has_expired(time.time() + 100)
        assert base_cache.has_expired(time.time() - 100)


class TestInMemoryCache(object):

    @mock.patch.object(mod.InMemoryCache, 'has_expired')
    def test_get_found(self, has_expired, im_cache):
        has_expired.return_value = False
        im_cache._cache['key'] = ('expires', 'data')
        assert im_cache.get('key') == 'data'
        has_expired.assert_called_once_with('expires')

    @mock.patch.object(mod.InMemoryCache, 'has_expired')
    def test_get_found_expired(self, has_expired, im_cache):
        has_expired.return_value = True
        im_cache._cache['key'] = ('expires', 'data')
        assert im_cache.get('key') is None
        has_expired.assert_called_once_with('expires')

    @mock.patch.object(mod.InMemoryCache, 'has_expired')
    def test_get_not_found(self, has_expired, im_cache):
        assert im_cache.get('key') is None
        assert not has_expired.called

    @mock.patch.object(mod.InMemoryCache, 'get_expiry')
    def test_set(self, get_expiry, im_cache):
        timeout = 300
        get_expiry.return_value = 'expires'
        im_cache.set('key', 'data', timeout=timeout)
        get_expiry.assert_called_once_with(timeout)
        assert im_cache._cache['key'] == ('expires', 'data')

    def test_clear(self, im_cache):
        im_cache._cache['key'] = 'test'
        im_cache.clear()
        assert im_cache._cache == {}

    def test_delete(self, im_cache):
        im_cache._cache['key'] = 'test'
        im_cache.delete('key')
        assert im_cache._cache == {}
        try:
            im_cache.delete('invalid')
        except Exception as exc:
            pytest.fail('Should not raise: {0}'.format(exc))

    def test_invalidate(self, im_cache):
        im_cache._cache['pre1_key1'] = 3
        im_cache._cache['pre1_key2'] = 4
        im_cache._cache['pre2_key1'] = 5
        im_cache.invalidate('pre1')
        assert im_cache._cache == {'pre2_key1': 5}


class TestScoredInMemoryCache(object):

    @mock.patch.object(mod.ScoredInMemoryCache, 'has_expired')
    def test_get_found(self, has_expired, sim_cache):
        has_expired.return_value = False
        sim_cache._cache['key'] = ('expires', 'data')
        sim_cache._scores['key'] = 0
        assert sim_cache.get('key') == 'data'
        assert sim_cache._scores['key'] == 1
        has_expired.assert_called_once_with('expires')

    @mock.patch.object(mod.ScoredInMemoryCache, 'delete')
    @mock.patch.object(mod.ScoredInMemoryCache, 'has_expired')
    def test_get_found_expired(self, has_expired, delete, sim_cache):
        has_expired.return_value = True
        sim_cache._cache['key'] = ('expires', 'data')
        assert sim_cache.get('key') is None
        has_expired.assert_called_once_with('expires')
        delete.assert_called_once_with('key')

    @mock.patch.object(mod.ScoredInMemoryCache, 'has_expired')
    def test_get_not_found(self, has_expired, sim_cache):
        assert sim_cache.get('key') is None
        assert not has_expired.called
        assert 'key' not in sim_cache._scores

    @mock.patch.object(mod.InMemoryCache, 'get_expiry')
    def test_set_cache_full_new_score(self, get_expiry):
        get_expiry.return_value = 'expires'
        sim_cache = mod.ScoredInMemoryCache(limit=3)
        sim_cache._cache['a'] = 'aa'
        sim_cache._cache['b'] = 'bb'
        sim_cache._cache['c'] = 'cc'
        sim_cache._scores['a'] = 10
        sim_cache._scores['b'] = 0
        sim_cache._scores['c'] = 3
        sim_cache.set('d', 'dd')
        assert sim_cache._cache == {'a': 'aa',
                                    'c': 'cc',
                                    'd': ('expires', 'dd')}
        assert sim_cache._scores == {'a': 10, 'c': 3, 'd': 0}

    def test_set_cache_full_keep_score(self, sim_cache):
        sim_cache._cache['a'] = 'aa'
        sim_cache._scores['a'] = 10
        sim_cache.set('a', 'newvalue')
        assert sim_cache._scores == {'a': 10}

    def test_clear(self, sim_cache):
        sim_cache._cache['key'] = 'val'
        sim_cache._scores['key'] = 10
        sim_cache.clear()
        assert sim_cache._cache == {}
        assert sim_cache._scores == {}

    def test_delete(self, sim_cache):
        sim_cache._cache['key'] = 'test'
        sim_cache._scores['key'] = 5
        sim_cache.delete('key')
        assert sim_cache._cache == {}
        assert sim_cache._scores == {}
        try:
            sim_cache.delete('invalid')
        except Exception as exc:
            pytest.fail('Should not raise: {0}'.format(exc))


class TestSizeScoredInMemoryCache(object):

    def test_set(self, ssim_cache):
        assert len(ssim_cache._sizes) == 0
        assert ssim_cache._cache_size == 0
        ssim_cache.set('a', 'simple')
        ssim_cache.set('b', 'complex')
        simple_size = sys.getsizeof('simple')
        complex_size = sys.getsizeof('complex')
        assert ssim_cache._sizes['a'] == simple_size
        assert ssim_cache._sizes['b'] == complex_size
        assert ssim_cache._cache_size == simple_size + complex_size

    def test_delete(self, ssim_cache):
        ssim_cache.set('a', 'simple')
        ssim_cache.set('b', 'complex')
        ssim_cache.delete('b')
        simple_size = sys.getsizeof('simple')
        assert ssim_cache._cache_size == simple_size
        assert ssim_cache._sizes['a'] == simple_size
        assert 'b' not in ssim_cache._sizes


class TestMemcachedCache(object):

    def test_no_client_lib(self):
        with pytest.raises(RuntimeError):
            with mock.patch.object(builtins,
                                   '__import__',
                                   side_effect=ImportError):
                mod.MemcachedCache(['127.0.0.1:11211'])

    def test_get(self, mc_cache):
        mc_cache.get('test')
        mc_cache._cache.get.assert_called_once_with('test')

    @mock.patch.object(mod.MemcachedCache, 'get_expiry')
    def test_set(self, get_expiry, mc_cache):
        get_expiry.return_value = 123456789
        mc_cache.set('key', 'data', timeout=120)
        mc_cache._cache.set.assert_called_once_with('key', 'data', 123456789)
        get_expiry.assert_called_once_with(120)

    def test_delete(self, mc_cache):
        mc_cache.delete('key')
        mc_cache._cache.delete.assert_called_once_with('key')

    def test_clear(self, mc_cache):
        mc_cache.clear()
        mc_cache._cache.flush_all.assert_called_once_with()

    @mock.patch.object(mod.MemcachedCache, 'set')
    @mock.patch.object(mod.uuid, 'uuid4')
    def test__new_prefix(self, uuid4, setfunc, mc_cache):
        uuid4.return_value = 'some-uuid-value'
        prefix = mc_cache._new_prefix('pre_')
        assert prefix == 'pre_some-uuid-value'
        prefix_key = mc_cache.prefixes_key + 'pre_'
        setfunc.assert_called_once_with(prefix_key, prefix, timeout=0)

    @mock.patch.object(mod.MemcachedCache, '_new_prefix')
    def test_parse_prefix(self, _new_prefix, mc_cache):
        _new_prefix.return_value = 'pre_some-uuid-value'
        prefix_key = mc_cache.prefixes_key + 'pre_'
        mc_cache._cache.get.return_value = None

        assert mc_cache.parse_prefix('pre_') == 'pre_some-uuid-value'
        mc_cache._cache.get.assert_called_once_with(prefix_key)
        _new_prefix.assert_called_once_with('pre_')

    @mock.patch.object(mod.MemcachedCache, '_new_prefix')
    def test_invalidate(self, _new_prefix, mc_cache):
        mc_cache.invalidate('test')
        _new_prefix.assert_called_once_with('test')
