"""
databases.py: Database utility functions

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os

import bottle

from .migrations import migrate
from .squery import Database, DatabaseContainer


def ensure_dir(path):
    """ Make sure directory at path exists """
    if not os.path.exists(path):
        os.makedirs(path)


def get_database_configs(conf):
    databases = dict()
    for pkg_name, db_names in conf['database.sources'].items():
        for name in db_names:
            databases[name] = dict(package_name=pkg_name)
    return databases


def get_databases(db_confs, host, port, user, password, debug=False):
    databases = dict((db_name, Database.connect(host,
                                                port,
                                                db_name,
                                                user,
                                                password,
                                                debug=debug))
                     for db_name, db_config in db_confs.items())
    return DatabaseContainer(databases)


def init_databases(config):
    database_configs = get_database_configs(config)
    databases = get_databases(database_configs,
                              config['database.host'],
                              config['database.port'],
                              config['database.user'],
                              config['database.password'],
                              debug=bottle.DEBUG)
    # Run migrations on all databases
    for db_name, db_config in database_configs.items():
        migration_pkg = '{0}.migrations.{1}'.format(db_config['package_name'],
                                                    db_name)
        migrate(databases[db_name], migration_pkg, config)

    return databases


def close_databases(databases):
    for db in databases.values():
        db.close()
