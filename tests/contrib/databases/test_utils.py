import mock

from librarian_core.contrib.databases import utils as mod


MOD = mod.__name__


@mock.patch(MOD + '.Database.connect')
def test_get_databases_connects(db_connect):
    """ When database name is passed as string, connection is made """
    mod.get_databases({'foo': {'package_name': 'foopkg', 'path': 'foo.db'}})
    db_connect.assert_called_once_with('foo.db')
