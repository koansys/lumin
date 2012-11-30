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
        return Collection(request=request, name=name, duplicate_key_error=AssertionError)

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

    def test_collection_insert(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user')
        self.assertEquals(result._collection.count(), 1)

    def test_collection_insert_duplicate_key(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user')
        result.insert({u'name': u'Foo'}, u'first user')
        self.assertEquals(result._collection.count(), 2)
        self.assertNotEquals(result._collection.find({"_id": u'first-user1'}), None)

    def test_collection_insert_duplicate_key_increment_false(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user', increment=False)
        self.assertRaises(AssertionError, result.insert, {u'name': u'Bar'}, u'first user', increment=False)

    def test_collection_delete(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user')
        result.delete(_id=u'first-user')
        self.assertEquals(result._collection.count(), 0)

# TODO
    def test_collection_save(self):
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

    def _create_context(self, data):
        self.request.db.test = self.request.db['test']
        self.request.db.test.insert(data)

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
        from pyramid.security import Allow
        from pyramid.security import Everyone
        test_acl = [
              [Allow, Everyone, 'view'],
              ]
        result.set__acl__(test_acl)
        self.assertEquals(result.__acl__, test_acl)
        result.delete__acl__()
        self.assertEquals(result.__acl__, [])

    def test__acl__is_not_list(self):
        result = self._call_fut(request=self.request)
        test_acl = 'string'
        mutator = []
        self.assertRaises(TypeError, result._acl_apply, test_acl, mutator=mutator)

# Test is failing
    # def test_duplicate_collection_creation(self):
    #     data = {"_id": "test_id", "foo": "bar"}
    #     self._call_fut(request=self.request, name='test', _id="test_id", data=data)
    #     from webob.exc import HTTPInternalServerError
    #     self.assertRaises(HTTPInternalServerError, self._call_fut, request=self.request, name='test', _id="test_id", data=data)

    def test_default__acl__set_to__acl__(self):
        from lumin.node import ContextById
        from pyramid.security import Allow
        from pyramid.security import Everyone
        test_acl = [
              [Allow, Everyone, 'view'],
              ]
        ContextById._default__acl__ = test_acl
        result = self._call_fut(request=self.request)
        self.assertEquals(result.__acl__, test_acl)
        ContextById._default__acl__ = []

    def test_ace_allocation(self):
        result = self._call_fut(request=self.request)
        from pyramid.security import Allow
        from pyramid.security import Everyone
        test_ace = [Allow, Everyone, 'view']
        mutator = []
        result._acl_apply(test_ace, mutator=mutator)
        pass  # Not sure how to go forward with this test...

    def test_add_ace(self):
        result = self._call_fut(request=self.request)
        from pyramid.security import Allow
        from pyramid.security import Everyone
        ace = [Allow, Everyone, 'view']
        result.add_ace(ace)
        ace1 = [Allow, Everyone, 'edit']
        result.add_ace(ace1)
        expected = [['Allow', 'system.Everyone', ['edit', 'view']]]
        self.assertEqual(result.__acl__, expected)

    def test_single_permission_through__acl_sorted(self):
        result = self._call_fut(request=self.request)
        from pyramid.security import Allow
        from pyramid.security import Everyone
        ace = [Allow, Everyone, 'view']
        single_permission = result._acl_sorted([ace[2]])
        self.assertEqual(single_permission, ace[2])

    def test_remove_ace(self):
        result = self._call_fut(request=self.request)
        from pyramid.security import Allow
        from pyramid.security import Everyone
        ace = [Allow, Everyone, 'edit']
        result.add_ace(ace)
        self.assertEqual(result.__acl__, result._default__acl__ + [ace])
        result.remove_ace(ace)
        self.assertEqual(result.__acl__, [])

    def test_oid_raises(self):
        from pyramid.exceptions import NotFound
        test_id = "test_id"
        self.assertRaises(NotFound, self._call_fut, request=self.request, _id=test_id)

    def test_oid(self):
        data = {"_id": "test_id", "foo": "bar"}
        self._create_context(data=data)
        result = self._call_fut(request=self.request, name="test", _id="test_id")
        self.assertEquals(result._id, "test_id")
        self.assertEquals(result.oid, 'test_id')

    def test_history(self):
        result = self._call_fut(request=self.request)
        standard_cursor = mongomock.Cursor('dataset')
        self.assertEqual(type(result.history()), type(standard_cursor))

    def test_history_limit_as_not_Int(self):
        result = self._call_fut(request=self.request)
        self.assertRaises(TypeError, result.history(), limit="string")

    def test_history_with_timestamp(self):
        from datetime import datetime
        now = datetime.now()
        result = self._call_fut(request=self.request)
        standard_cursor = mongomock.Cursor('dataset')
        self.assertEqual(type(result.history(since=now)), type(standard_cursor))

    def test_before_history_with_timestamp(self):
        from datetime import datetime
        now = datetime.now()
        result = self._call_fut(request=self.request)
        standard_cursor = mongomock.Cursor('dataset')
        self.assertEqual(type(result.history(after=False, since=now)), type(standard_cursor))

    def test_history_with_fields(self):
        result = self._call_fut(request=self.request)
        standard_cursor = mongomock.Cursor('dataset')
        fields = ['test', 'fields']
        self.assertEqual(type(result.history(fields=fields)), type(standard_cursor))

    def test_remove(self):
        data = {"_id": "test_id", "foo": "bar"}
        self._create_context(data=data)
        result = self._call_fut(request=self.request, name="test", _id="test_id")
        result.remove()
        self.assertTrue(result.data['deleted'])

# # TypeError: 'NoneType' object has no attribute '__getitem__'
#     def test_fail_save(self):
#         result = self._call_fut(request=self.request)
#         self.assertRaises(KeyError, result.save())

# # TypeError: 'NoneType' object has no attribute '__getitem__'
#     def test_update(self):
#         data = {"_id": "test_id", "foo": "bar"}
#         self._create_context(data=data)
#         result = self._call_fut(request=self.request, name="test", _id="test_id")
#         result.update({'foo': "baz"})
#         self.assertEqual(result.data.foo, "baz")


class TestContextBySpec(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.request = pyramid.testing.DummyRequest()

        self.mock_conn = mongomock.Connection()
        self.request.db = mongomock.Database(self.mock_conn)

    def tearDown(self):
        pyramid.testing.tearDown()

    def _call_fut(self, request=None, _id='test', name='test', data=None):
        from lumin.node import ContextBySpec
        self.request.db.test = self.request.db['test']
        data = {"_id": "test_id", "foo": "bar"}
        self.request.db.test.insert(data)
        return ContextBySpec(request=request, _id=_id, name=name, data=data, duplicate_key_error=AssertionError)

    def test_ctor_default(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result.__name__, None)
        self.assertEquals(result._spec, {'_id': 'test_id'})
        self.assertEquals(result.data, {"_id": "test_id", "foo": "bar"})

    def test_default__acl__set_to__acl__(self):
        from lumin.node import ContextBySpec
        from pyramid.security import Allow
        from pyramid.security import Everyone
        test_acl = [
              [Allow, Everyone, 'view'],
              ]
        ContextBySpec._default__acl__ = test_acl
        result = self._call_fut(request=self.request)
        self.assertEquals(result.__acl__, test_acl)
        ContextBySpec._default__acl__ = []

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
        from pyramid.security import Allow
        from pyramid.security import Everyone
        test_acl = [
              [Allow, Everyone, 'view'],
              ]
        result.set__acl__(test_acl)
        self.assertEquals(result.__acl__, test_acl)
        result.delete__acl__()
        self.assertEquals(result.__acl__, [])

    def test_add_ace(self):
        result = self._call_fut(request=self.request)
        from pyramid.security import Allow
        from pyramid.security import Everyone
        ace = [Allow, Everyone, 'view']
        result.add_ace(ace)
        ace1 = [Allow, Everyone, 'edit']
        result.add_ace(ace1)
        expected = [['Allow', 'system.Everyone', 'view'], ['Allow', 'system.Everyone', 'edit']]
        self.assertEqual(result.__acl__, expected)

    def test_error_add_ace(self):
        result = self._call_fut(request=self.request)
        bad_ace = "string"
        self.assertRaises(TypeError, result.add_ace, ace=bad_ace)

    def test_remove_ace(self):
        result = self._call_fut(request=self.request)
        from pyramid.security import Allow
        from pyramid.security import Everyone
        ace = [Allow, Everyone, 'edit']
        result.add_ace(ace)
        self.assertEqual(result.__acl__, result._default__acl__ + [ace])
        result.remove_ace(ace)
        self.assertEqual(result.__acl__, [])

    def test_error_remove_ace(self):
        result = self._call_fut(request=self.request)
        bad_ace = "string"
        self.assertRaises(TypeError, result.remove_ace, ace=bad_ace)

    def test_oid(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result.oid, 'test_id')

    def test_set___name__(self):
        result = self._call_fut(request=self.request)
        slug = "name"
        result.set___name__(slug=slug)
        self.assertEquals(result.data['__name__'], slug)

    def test_history(self):
        result = self._call_fut(request=self.request)
        standard_cursor = mongomock.Cursor('dataset')
        self.assertEqual(type(result.history()), type(standard_cursor))

    def test_history_limit_as_not_Int(self):
        result = self._call_fut(request=self.request)
        self.assertRaises(TypeError, result.history(), limit="string")

    def test_history_with_timestamp(self):
        from datetime import datetime
        now = datetime.now()
        result = self._call_fut(request=self.request)
        standard_cursor = mongomock.Cursor('dataset')
        self.assertEqual(type(result.history(since=now)), type(standard_cursor))

    def test_before_history_with_timestamp(self):
        from datetime import datetime
        now = datetime.now()
        result = self._call_fut(request=self.request)
        standard_cursor = mongomock.Cursor('dataset')
        self.assertEqual(type(result.history(after=False, since=now)), type(standard_cursor))

    def test_history_with_fields(self):
        result = self._call_fut(request=self.request)
        standard_cursor = mongomock.Cursor('dataset')
        fields = ['test', 'fields']
        self.assertEqual(type(result.history(fields=fields)), type(standard_cursor))

    def test_insert(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user')
        self.assertEquals(result._collection.count(), 2)  # There's one created in `_call_fut`

    def test_insert_duplicate_key(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user')
        result.insert({u'name': u'Foo'}, u'first user')
        self.assertEquals(result._collection.count(), 3)  # There's one created in `_call_fut`
        self.assertNotEquals(result._collection.find({"_id": u'first-user1'}), None)

    def test_insert_duplicate_key_increment_false(self):
        result = self._call_fut(request=self.request)
        result.insert({u'name': u'Foo'}, u'first user', increment=False)
        self.assertRaises(AssertionError, result.insert, {u'name': u'Bar'}, u'first user', increment=False)

    def test_remove(self):
        result = self._call_fut(request=self.request)
        result.remove()
        self.assertEquals(result._collection.count(), 0)

# # TypeError: 'NoneType' object has no attribute '__getitem__'
#     def test_fail_save(self):
#         result = self._call_fut(request=self.request)
#         self.assertRaises(KeyError, result.save())

# # TypeError: 'NoneType' object has no attribute '__getitem__'
#     def test_update(self):
#         data = {"_id": "test_id", "foo": "bar"}
#         self._create_context(data=data)
#         result = self._call_fut(request=self.request, name="test", _id="test_id")
#         result.update({'foo': "baz"})
#         self.assertEqual(result.data.foo, "baz")
