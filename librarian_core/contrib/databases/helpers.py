"""
databases.py: Database utility functions

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os

import bottle

from squery import Database, DatabaseContainer


POSTGRES_BACKEND = 'postgres'
SQLITE_BACKEND = 'sqlite'
SQLIZATOR_BACKEND = 'sqlizator'
PATHS_CONFIGURABLE = (SQLITE_BACKEND, SQLIZATOR_BACKEND)


def is_path_configurable(conf):
    return conf['database.backend'] in PATHS_CONFIGURABLE


def ensure_dir(path):
    """ Make sure directory at path exists """
    if not os.path.exists(path):
        os.makedirs(path)


def get_database_path(conf, name):
    return os.path.abspath(os.path.join(conf['database.path'], name + '.db'))


def get_database_configs(conf):
    databases = dict()
    for pkg_name, db_names in conf['database.sources'].items():
        for name in db_names:
            databases[name] = dict(package_name=pkg_name,
                                   database=name,
                                   path=get_database_path(conf, name))
    return databases


def get_databases(db_confs, backend, host, port, user, password, debug=False):
    databases = dict((name, Database.connect(backend,
                                             host=host,
                                             port=port,
                                             database=db_config['database'],
                                             path=db_config['path'],
                                             user=user,
                                             password=password,
                                             debug=debug))
                     for name, db_config in db_confs.items())
    return DatabaseContainer(databases, debug=debug)


def init_databases(config):
    database_configs = get_database_configs(config)
    if is_path_configurable(config):
        # Make sure all necessary directories are present
        for db_config in database_configs.values():
            ensure_dir(os.path.dirname(db_config['path']))

    databases = get_databases(database_configs,
                              config['database.backend'],
                              config['database.host'],
                              config['database.port'],
                              config['database.user'],
                              config['database.password'],
                              debug=bottle.DEBUG)
    # Run migrations on all databases
    for db_name, db_config in database_configs.items():
        migration_pkg = '{0}.migrations.{1}'.format(db_config['package_name'],
                                                    db_name)
        Database.migrate(databases[db_name], migration_pkg, config)

    return databases


def close_databases(databases):
    for db in databases.values():
        db.close()
