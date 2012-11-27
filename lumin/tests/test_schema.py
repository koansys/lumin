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

    def test_username_too_short_raises(self):
        from colander import Invalid
        self.assertRaises(
            Invalid,
            self._call_fut, 'aaa'
            )

    def test_username_too_short_exception(self):
        from colander import Invalid
        result = None
        try:
            result = self._call_fut('aaa')
        except Invalid as e:
            self.assertEquals(e.msg, "Length of user name must be between 4 and \
                                    24 lowercase alphanumeric characters")
        self.failUnless(result is None)

    def test_username_too_long_exception(self):
        from colander import Invalid
        import string
        result = None
        try:
            result = self._call_fut(string.ascii_lowercase)
        except Invalid as e:
            self.assertEquals(e.msg, "Length of user name must be between 4 and \
                                    24 lowercase alphanumeric characters")
        self.failUnless(result is None)

    def test_username_not_lower_exception(self):
        from colander import Invalid
        result = None
        try:
            result = self._call_fut("AAAA")
        except Invalid as e:
            self.assertEquals(e.msg,
                                "Only lowercase numbers, letters and \
                                underscores are permitted")
        self.failUnless(result is None)

    def test_username_has_special_char_exception(self):
        from colander import Invalid
        result = None
        try:
            result = self._call_fut("asn$sldkjf")
        except Invalid as e:
            self.assertEquals(e.msg,
                                "Only lowercase numbers, letters and \
                                underscores are permitted")
        self.failUnless(result is None)

    def test_username_has_space_exception(self):
        from colander import Invalid
        result = None
        try:
            result = self._call_fut(" asnsldkjf")
        except Invalid as e:
            self.assertEquals(e.msg,
                                "Only lowercase numbers, letters and \
                                underscores are permitted")
        self.failUnless(result is None)

    def test_username_not_alpha_start_exception(self):
        from colander import Invalid
        result = None
        try:
            result = self._call_fut("3asnsldkjf")
        except Invalid as e:
            self.assertEquals(e.msg,
                                "The username must start with a \
                                   letter")
        self.failUnless(result is None)

    def test_username_not_available(self):
        from colander import Invalid
        result = None
        try:
            result = self._call_fut("aname")
        except Invalid as e:
            self.assertEquals(e.msg, "Username is not available")
        self.failUnless(result is None)

    def test_username_available(self):
        from colander import Invalid
        result = None
        try:
            result = self._call_fut("available_name")
        except Invalid as e:
            self.failIf(e)
        self.assertEquals(result, None)
