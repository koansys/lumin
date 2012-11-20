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

    def _create_collection_by_id(self, _id=0, name="test_name"):
        from lumin.node import ContextById
        return ContextById(request=self.request, _id=_id, name=name)

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

    def test_collection_find(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result.find().count(), 0)

    def test_collection_get(self):
        data = self._create_collection_by_id()

        result = self._call_fut(request=self.request)
        self.assertEquals(result.get(_id=0).__name__, data.__name__)

    # TODO - Need to work out MongoMock's handeling of safe...
    # def test_collection_insert(self):
    #     result = self._call_fut(request=self.request)
    #     result.insert({u'name': u'Foo'}, u'first user')
    #     self.assertEquals(result._collection.count(), 1)

    # TODO - Need to work out MongoMock's handeling of safe...
    # def test_collection_insert_duplicate_key(self):
    #     result = self._call_fut(request=self.request)
    #     result.insert({u'name': u'Foo'}, u'first user')
    #     result.insert({u'name': u'Bar'}, u'first user')
    #     self.assertRaises(AssertionError)

    # TODO - Need to work out MongoMock's handeling of safe...
    # def test_collection_delete(self):
    #     result = self._call_fut(request=self.request)
    #     result.insert({u'name': u'Foo'}, u'first user')
    #     result.delete(_id=u'first-user')
    #     self.assertEquals(result._collection.count(), 0)

    def test_collection_save(self):  # TODO
        pass


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
