import os
import unittest

import pyramid.testing


class BaseFunctionalTestCase(unittest.TestCase):
    request_path = '/'

    def setUp(self):
        self.request = pyramid.testing.DummyRequest(
            path=self.request_path,
            )

        self.config = pyramid.testing.setUp(
            request=self.request,
            settings={
                'secret': 'secret',
                'db_name': 'test',
                })

        self.config.include('lumin')

        conn = self.config.register_mongodb(
            'mongodb://%s' % os.environ['TEST_MONGODB'])

        # Drop and create test database
        conn.drop_database('test')
        db = conn['test']

        # Create collections
        db.create_collection('users')

        # Fire new request event to set up environment
        self.config.registry.handle(pyramid.events.NewRequest(self.request))

    def tearDown(self):
        pyramid.testing.tearDown()
