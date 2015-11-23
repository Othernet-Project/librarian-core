"""
sqery.py: Helpers for working with databases

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from __future__ import print_function

import contextlib
import logging
import os
import re

import fdb as dblib

from bottle_utils.common import basestring
from bottle_utils.lazy import CachingLazy
from sqlize import (From, Where, Group, Order, Limit, Select, Update, Delete,
                    Insert, Replace, sqlin, sqlarray)


SLASH = re.compile(r'\\')
MAX_VARIABLE_NUMBER = 999


class Connection(object):
    """ Wrapper for dblib.Connection object """
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connect()

    def connect(self):
        connector = dblib.connect
        if not os.path.exists(self.database):
            connector = dblib.create_database

        self._conn = connector(host=self.host,
                               port=self.port,
                               database=self.database,
                               user=self.user,
                               password=self.password)
        logging.debug('Connected to database {}'.format(self.dsn))

    def close(self):
        self._conn.commit()
        self._conn.close()

    @property
    def dsn(self):
        return '{}:{}/{}'.format(self.host, self.port, self.database)

    def __getattr__(self, attr):
        conn = object.__getattribute__(self, '_conn')
        return getattr(conn, attr)

    def __setattr__(self, attr, value):
        if not hasattr(self, attr) or attr == '_conn':
            object.__setattr__(self, attr, value)
        else:
            setattr(self._conn, attr, value)

    def __repr__(self):
        return "<Connection '%s'>" % self.dsn


class Database(object):

    # Provide access to query classes for easier access
    sqlin = staticmethod(sqlin)
    sqlarray = staticmethod(sqlarray)
    From = From
    Where = Where
    Group = Group
    Order = Order
    Limit = Limit
    Select = Select
    Update = Update
    Delete = Delete
    Insert = Insert
    Replace = Replace
    MAX_VARIABLE_NUMBER = MAX_VARIABLE_NUMBER

    def __init__(self, conn, debug=False):
        self.conn = conn
        self.debug = debug
        self._cursor = None

    def _convert_query(self, qry):
        """ Ensure any SQLExpression instances are serialized

        :param qry:     raw SQL string or SQLExpression instance
        :returns:       raw SQL string
        """
        if hasattr(qry, 'serialize'):
            qry = qry.serialize()
        assert isinstance(qry, basestring), 'Expected qry to be string'
        if self.debug:
            print('SQL:', qry)
        return qry

    def query(self, qry, *params, **kwparams):
        """ Perform a query

        Any positional arguments are converted to a list of arguments for the
        query, and are used to populate any '?' placeholders. The keyword
        arguments are converted to a mapping which provides values to ':name'
        placeholders. These do not apply to SQLExpression instances.

        :param qry:     raw SQL or SQLExpression instance
        :returns:       cursor object
        """
        qry = self._convert_query(qry)
        self.cursor.execute(qry, params or kwparams)
        return self.cursor

    def execute(self, qry, *args, **kwargs):
        qry = self._convert_query(qry)
        self.cursor.execute(qry, *args, **kwargs)

    def executemany(self, qry, *args, **kwargs):
        qry = self._convert_query(qry)
        self.cursor.executemany(qry, *args, **kwargs)

    def executescript(self, sql):
        self.cursor.executescript(sql)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
        self.conn.commit()

    def refresh_table_stats(self):
        self.execute('ANALYZE sqlite_master;')

    def acquire_lock(self):
        self.execute('BEGIN EXCLUSIVE;')

    def close(self):
        self.conn.close()
        # the cached cursor object must be reset, otherwise after reconnecting
        # it would still try to use it, and would run into the closed db issue
        self._cursor = None

    def reconnect(self):
        self.conn.connect()

    @property
    def connection(self):
        return self.conn

    @property
    def cursor(self):
        if self._cursor is None:
            self._cursor = self.conn.cursor()
        return self._cursor

    @property
    def results(self):
        return self.cursor.fetchall()

    @property
    def result(self):
        return self.cursor.fetchone()

    @contextlib.contextmanager
    def transaction(self, silent=False):
        self.execute('BEGIN;')
        try:
            yield self.cursor
            self.commit()
        except Exception:
            self.rollback()
            if silent:
                return
            raise

    @classmethod
    def connect(cls, host, port, path, user, password):
        return Connection(host, port, path, user, password)

    def __repr__(self):
        return "<Database connection='%s'>" % self.conn.dsn


class DatabaseContainer(dict):
    def __init__(self, connections, debug=False):
        super(DatabaseContainer, self).__init__(
            {n: CachingLazy(Database, c, debug=debug)
             for n, c in connections.items()})
        self.__dict__ = self
