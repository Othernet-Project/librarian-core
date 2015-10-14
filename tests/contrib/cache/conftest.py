import pytest

from librarian_core.contrib.cache import backends as mod


@pytest.fixture
def base_cache():
    return mod.BaseCache()


@pytest.fixture
def im_cache():
    return mod.InMemoryCache()


@pytest.fixture
def sim_cache():
    return mod.ScoredInMemoryCache(limit=0)


@pytest.fixture
def ssim_cache():
    return mod.SizeScoredInMemoryCache(limit=0)
