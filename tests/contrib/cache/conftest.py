import pytest

from librarian_core.contrib.cache import cache as mod


@pytest.fixture
def base_cache():
    return mod.BaseCache()


@pytest.fixture
def im_cache():
    return mod.InMemoryCache()


@pytest.fixture
def sim_cache():
    return mod.ScoredInMemoryCache()
