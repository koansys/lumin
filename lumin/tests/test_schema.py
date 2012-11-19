from __future__ import unicode_literals
import unittest

import mongomock

import pyramid.testing

from lumin.testing import DummySchemaNode


class TestUsernameValidator(unittest.TestCase):

    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.request = pyramid.testing.DummyRequest()
        self.mock_conn = mongomock.Connection()
        self.request.db = mongomock.Database(self.mock_conn)
        self.request.db.users = mongomock.Collection(self.request.db)
        self.request.db.users.insert(
            {'_id': 'aname', 'bar': 'baz'}
            )

        class DummyContext:
            def __init__(self, request):
                self.request = request

            def find(self, **kwargs):
                return self.request.db.users.find(kwargs)

        self.request.context = DummyContext(self.request)

    def tearDown(self):
        pyramid.testing.tearDown()

    def _call_fut(self, value):
        from lumin.schema import deferred_username_validator
        node = DummySchemaNode('username')
        func = deferred_username_validator(node, {"request": self.request})
        return func(node, value)

    def test_username_too_short(self):
        from colander import Invalid
        self.assertRaises(
            Invalid,
            self._call_fut, 'aname'
            )
