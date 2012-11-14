# import os
import unittest

import mongomock

import pyramid.testing


class TestConfiguration(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()

    def tearDown(self):
        pyramid.testing.tearDown()

    def _includelumin(self):
        import lumin
        self.config.include(lumin)

    def _registerdb(self):
        conn = Connection()
        self.config.registry.settings['db_name'] = 'frozznob'
        self.config.register_mongodb('mongodb://localhost', conn=conn)

    def test_register_mongodb_directive(self):
        self._includelumin()

        from lumin.db import IMongoDBConnection
        connection = self.config.registry.queryUtility(IMongoDBConnection)
        self.assertTrue(connection is None)

        # Now, let's register a database connection
        self._registerdb()
        connection = self.config.registry.queryUtility(IMongoDBConnection)
        self.assertTrue(connection is not None)

    def test_get_mongodb(self):
        self._includelumin()
        self._registerdb()

        from lumin.db import get_mongodb
        from mongomock import Database

        conn = get_mongodb(self.config.registry)
        self.assertTrue(isinstance(conn, Database))

    def test_add_mongodb(self):
        self._includelumin()
        self._registerdb()
        import pyramid
        request = pyramid.testing.DummyRequest(
            path='/',
            )
        import pyramid
        # fire an event to call add_mongodb
        self.config.registry.handle(pyramid.events.NewRequest(request))
        self.assertTrue(hasattr(request, 'db'))


class TestIncludeMe(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()

    def tearDown(self):
        pyramid.testing.tearDown()

    def test_includeme(self):
        import lumin
        self.assertFalse(hasattr(self.config, 'register_mongodb'))
        lumin.includeme(self.config)
        self.assertTrue(hasattr(self.config, 'register_mongodb'))


class Database(mongomock.Database):
    def __init__(self, conn):
        super(Database, self).__init__(conn)

    def __getitem__(self, db_name):
        db = self._collections.get(db_name, None)
        if db is None:
            db = self._collections[db_name] = Collection(self)
        return db

    def __getattr__(self, attr):
        return self[attr]


class Connection(mongomock.Connection):
    def __init__(self):
        super(Connection, self).__init__()

    def __getitem__(self, db_name):
        db = self._databases.get(db_name, None)
        if db is None:
            db = self._databases[db_name] = Database(self)
        return db

    def __getattr__(self, attr):
        return self[attr]


class Collection(mongomock.Collection):
    def __call__(self, *args, **kwargs):
        pass
