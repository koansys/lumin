from __future__ import unicode_literals
import unittest

import mongomock

# Mongomock barfs on inserting keys differently than Pymongo. Expecting `DuplicateKeyError` not `AssertionError`
# from pymongo.errors import DuplicateKeyError

from webob.exc import HTTPInternalServerError

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
        self.assertIsNone(result.__name__)

    def test_factory_parent(self):
        result = self._call_fut(request=self.request)
        self.assertIsNone(result.__parent__)


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
        self.assertIsNone(result.__name__)
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
    def test_collection_insert(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user')
        self.assertEquals(result._collection.count(), 1)
    # Mongomock barfs on inserting keys differently than Pymongo. Expecting `DuplicateKeyError` not `AssertionError`
    # This does not trigger line 88 on node.py
    # def test_collection_insert_duplicate_key(self):
    #     result = self._call_fut(request=self.request)
    #     result.insert({u'name': u'Foo'}, u'first user')
    #     self.assertRaises(AssertionError, result.insert, {u'name': u'Bar'}, u'first user')

    # Works when node.py is expecting AssertionError
    def test_collection_insert_duplicate_key(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user')
        result.insert({u'name': u'Foo'}, u'first user')
        self.assertEquals(result._collection.count(), 2)
        self.assertNotEquals(result._collection.find({"_id": u'first-user1'}), None)

    # Mongomock barfs on inserting keys differently than Pymongo. Expecting `DuplicateKeyError` not `AssertionError`
    def test_collection_insert_duplicate_key_increment_false(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user', increment=False)
        self.assertRaises(AssertionError, result.insert, {u'name': u'Bar'}, u'first user', increment=False)

    # TODO - Need to work out MongoMock's handeling of safe...
    def test_collection_delete(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user')
        result.delete(_id=u'first-user')
        self.assertEquals(result._collection.count(), 0)

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
        self.assertIsNone(result.__name__)
        self.assertIsNone(result._id)
        self.assertEquals(result._spec, {'_id': None})
        self.assertEquals(result.data, {})

    def test_get__acl__(self):
        result = self._call_fut(request=self.request)
        acl = result.get__acl__()
        self.assertEquals(acl, [])

    def test_set__acl__(self):
        from pyramid.security import Allow
        from pyramid.security import Everyone
        test_acl = [
              [Allow, Everyone, 'view'],
              ]
        result = self._call_fut(request=self.request)
        result.set__acl__(test_acl)
        self.assertEquals(result.__acl__, test_acl)

    def test_delete__acl__(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result.__acl__, [])

    def test__acl__is_not_list(self):
        result = self._call_fut(request=self.request)
        test_acl = 'string'
        mutator = []
        self.assertRaises(TypeError, result._acl_apply, test_acl, mutator=mutator)

    # # TODO - Figure out how to mock HTTP for line 146 in node.py
    # def test_duplicate_collection_creation(self):
    #     self._call_fut(request=self.request, _id='test')
    #     self.assertRaises(HTTPInternalServerError, self._call_fut, request=self.request, _id='test')

    # # This destroys many tests above since it puts test_acl onto ContextById permentally.
    # def test_default__acl__set_to__acl__(self):
    #     from lumin.node import ContextById
    #     from pyramid.security import Allow
    #     from pyramid.security import Everyone

    #     test_acl = [
    #           [Allow, Everyone, 'view'],
    #           ]
    #     ContextById._default__acl__ = test_acl
    #     result = self._call_fut(request=self.request)
    #     self.assertEquals(result.__acl__, test_acl)
    #     self.tearDown()


# # TODO - Figure out how to mock HTTP for line 388 in node.py
# class TestContextBySpec(unittest.TestCase):
#     def setUp(self):
#         self.config = pyramid.testing.setUp()
#         self.request = pyramid.testing.DummyRequest()

#         self.mock_conn = mongomock.Connection()
#         self.request.db = mongomock.Database(self.mock_conn)

#     def tearDown(self):
#         pyramid.testing.tearDown()

#     def _call_fut(self, request=None, _id='test', name=None, data=None):
#         from lumin.node import ContextBySpec
#         return ContextBySpec(request=request, _id=_id, name=name, data=data)

#     def test_ctor_default(self):
#         result = self._call_fut(request=self.request)
#         self.assertEquals(result.__name__, None)
#         self.assertEquals(result._spec, {'_id': None})
#         self.assertEquals(result.data, {})

#     def test_get__acl__(self):
#         result = self._call_fut(request=self.request)
#         acl = result.get__acl__()
#         self.assertEquals(acl, [])

#     def test_set__acl__(self):
#         from pyramid.security import Allow
#         from pyramid.security import Everyone
#         test_acl = [
#               [Allow, Everyone, 'view'],
#               ]
#         result = self._call_fut(request=self.request)
#         result.set__acl__(test_acl)
#         self.assertEquals(result.__acl__, test_acl)

#     def test_delete__acl__(self):
#         result = self._call_fut(request=self.request)
#         self.assertEquals(result.__acl__, None)
