from __future__ import unicode_literals
import unittest

import mongomock

import pyramid.testing


class TestFactory(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.request = pyramid.testing.DummyRequest()

    def tearDown(self):
        pyramid.testing.tearDown()

    def _call_fut(self, request=None):
        from lumin.node import Factory
        return Factory(request=request)

    def test_ctor_default(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result, result)

    def test_default_acl(self):
        result = self._call_fut(request=self.request)
        default_acl = [['Allow', 'system.Everyone', u'view']]
        self.assertEquals(result._default__acl__, default_acl)

    def test_acl(self):
        result = self._call_fut(request=self.request)
        acl = [['Allow', 'system.Everyone', u'view']]
        self.assertEquals(result.__acl__, acl)

    def test_factory_name(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result.__name__, None)

    def test_factory_parent(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result.__parent__, None)


class TestCollection(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.request = pyramid.testing.DummyRequest()

        self.mock_conn = mongomock.Connection()
        self.request.db = mongomock.Database(self.mock_conn)

    def tearDown(self):
        pyramid.testing.tearDown()

    def _call_fut(self, request=None, name=None):
        from lumin.node import Collection
        return Collection(request=request, name=name)

    def test_ctor_default(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result.__name__, None)
        self.assertEquals(result._collection.count(), 0)
        self.assertEquals(result._collection_history.count(), 0)

    def test_ctor_with_name(self):
        result = self._call_fut(request=self.request, name="test_name")
        self.assertEquals(result.__name__, "test_name")
        self.assertEquals(result._collection.count(), 0)
        self.assertEquals(result._collection_history.count(), 0)

    # def test__name__property(self):


class TestContextById(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.request = pyramid.testing.DummyRequest()

        self.mock_conn = mongomock.Connection()
        self.request.db = mongomock.Database(self.mock_conn)

    def tearDown(self):
        pyramid.testing.tearDown()

    def _call_fut(self, request=None, _id=None, name=None, data=None):
        from lumin.node import ContextById
        return ContextById(request=request, _id=_id, name=name, data=data)

    def test_ctor_default(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result.__name__, None)
        self.assertEquals(result._id, None)
        self.assertEquals(result._spec, {'_id': None})
        self.assertEquals(result.data, {})


class TestContextBySpec(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.request = pyramid.testing.DummyRequest()

        self.mock_conn = mongomock.Connection()
        self.request.db = mongomock.Database(self.mock_conn)

    def tearDown(self):
        pyramid.testing.tearDown()

    def _call_fut(self, request=None, _id=None, name=None, data=None):
        from lumin.node import ContextBySpec
        return ContextBySpec(request=request, _id=_id, name=name, data=data)

    def test_ctor_default(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result.__name__, None)
        self.assertEquals(result._spec, {'_id': None})
        self.assertEquals(result.data, {})
