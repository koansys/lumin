import unittest

import pyramid


class TestDB(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()

    def tearDown(self):
        pyramid.testing.tearDown()

    def test_register_mongodb(self):
        import os
        import lumin
        import pymongo
        ## shouldn't be able to connect to example.com
        self.assertRaises(pymongo.errors.AutoReconnect,
            lumin.db.register_mongodb,
            self.config, "localhost:65536"
            )
        conn = lumin.db.register_mongodb(
            self.config,
            os.environ.get("TEST_MONGODB")
            )
        self.assertTrue(conn)



