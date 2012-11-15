from __future__ import unicode_literals

from lumin.testing.base import BaseFunctionalTestCase


class CollectionTestCase(BaseFunctionalTestCase):
    def test_collection_find(self):
        # Insert item directly into collection
        self.request.db['test'].insert({'_id': 'frobnitz'}, {})

        from lumin.node import Collection
        collection = Collection(self.request, 'test')

        items = tuple(collection.find(_id='frobnitz'))
        self.assertEqual(len(items), 1)

        items = tuple(collection.find(_id='frobnozz'))
        self.assertEqual(len(items), 0)

    def test_collection_get(self):
        # Insert item directly into collection
        self.request.db['test'].insert({'_id': 'frobnitz'}, {})

        from lumin.node import Collection
        collection = Collection(self.request, 'test')

        item = collection.get('frobnitz')
        self.assertEqual(item.collection, 'test')

    def test_collection_delete(self):
        # Insert item directly into collection
        self.request.db['test'].insert({'_id': 'frobnitz'}, {})

        from lumin.node import Collection
        collection = Collection(self.request, 'test')
        result = collection.delete('frobnitz')
        items = tuple(collection.find(_id='frobnitz'))
        self.assertEqual(len(items), 0)
        self.assertEqual(result, None)

    def test_collection_insert(self):
        from lumin.node import Collection
        collection = Collection(self.request, 'test')

        result = collection.insert(
            {'_id': 'frobnitz'}, 'Frobnitz')
        self.assertEqual(result, 'frobnitz')

        # Insert another, with "increment" enabled
        result = collection.insert(
            {'_id': 'frobnitz'}, 'Frobnitz', increment=True)
        self.assertEqual(result, 'frobnitz-1')


class ContextByIdTestCase(BaseFunctionalTestCase):

    def test_context_with_data(self):
        """A context can be constructed directly from document data.
        """
        from lumin.node import ContextById
        self.request.db['test'].insert(
            {'_id': 'frobnitz', 'title': 'Frobnitz'})
        doc = self.request.db['test'].find_one({'_id': 'frobnitz'})
        context = ContextById(self.request, 'frobnitz', 'test', data=doc)
        self.assertEqual(
            context.data, {'_id': 'frobnitz', 'title': 'Frobnitz'})
        context.data['abc'] = 123
        context.save()
        doc = self.request.db['test'].find_one({'_id': 'frobnitz'})
        doc.pop('mtime')

        self.assertEqual(
            doc,
            dict(_id='frobnitz', title='Frobnitz', abc=123, changed_by=''))

    def test_context_with_data_sans_document(self):
        """A context without a document raises errors on lifecycle methods.
        """
        from lumin.node import ContextById
        data = {'_id': 'foobar', 'title': 'hello world'}
        context = ContextById(self.request, 'frobnitz', 'test', data=data)
        self.assertEqual(context.data, data)
        self.assertRaises(KeyError, context.save)
        # remove still works without error, but factoring in
        # concurrency, its fine, as its the same end state.

    def test_save(self):
        from lumin.node import ContextById
        # Insert item directly into collection
        self.request.db['test'].insert(
            {'_id': 'frobnitz'}, {'title': 'Frobnitz'}
            )

        context = ContextById(self.request, 'frobnitz', 'test')
        context.data.update({'title': 'Frobbozz'})
        context.save()
        history = context.history()
        self.assertEquals(history.count(), 0)
        self.assertRaises(StopIteration, next, history)
        self.assertTrue(context.data['mtime'])

    def test_update(self):
        # Insert item directly into collection
        self.request.db['test'].insert(
            {'_id': 'frobnitz'}, {'title': 'Frobnitz'}
            )

        from lumin.node import ContextById
        context = ContextById(self.request, 'frobnitz', 'test')
        result = context.update({'title': 'Frobbozz'})
        self.assertEqual(result, None)
        self.assertEqual(context.data['title'], 'Frobbozz')

        data = next(self.request.db['test'].find({'_id': 'frobnitz'}))
        self.assertEqual(data['title'], context.data['title'])
        self.assertEqual(data['changed_by'], '')
        self.assertTrue(data['mtime'])

    def test_update_history(self):
        # Insert item directly into collection
        self.request.db['test'].insert({'_id': 'frobnitz', 'title': ''})

        from lumin.node import ContextById
        context = ContextById(self.request, 'frobnitz', 'test')

        # Update 1
        context.update({'title': 'Frobnitz'})

        # Update 2
        context.update({'title': 'Frobbozz'})

        history = context.history()

        self.assertEqual(history.count(), 2)
        obj = next(history)
        self.assertEqual(obj['title'], 'Frobnitz')
        self.assertNotEqual(obj['mtime'], context.data['mtime'])
        #import pdb; pdb.set_trace()
        self.assertEqual(next(history)['title'], '')
        self.assertEqual(context.data['title'], 'Frobbozz')

    def test_empty_default__acl__(self):
        self.request.db['test'].insert({'_id': 'frobnitz', 'title': ''})

        from lumin.node import ContextById

        context = ContextById(self.request, 'frobnitz', 'test')
        self.assertEquals(context.__acl__, [])

        context.__acl__ = [[1, 2, 3]]
        self.assertEquals(context.__acl__, [[1, 2, 3]])
        context.save()
        document = self.request.db['test'].find_one({'_id': 'frobnitz'})
        self.failUnless(document.get('__acl__', None), [[1, 2, 3]])

        del context.__acl__
        self.assertEquals(context.__acl__, [])
        context.save()
        document = self.request.db['test'].find_one({'_id': 'frobnitz'})
        self.failIf(document.get('__acl__', None))

    def test_with_default__acl__(self):
        self.request.db['test'].insert({'_id': 'frobnitz', 'title': ''})
        from lumin.node import ContextById

        class AContext(ContextById):
            _default__acl__ = [[1, 2, 3]]

        context = AContext(self.request, 'frobnitz', 'test')
        self.assertEquals(context.__acl__, [[1, 2, 3]])
        context.save()
        document = self.request.db['test'].find_one({'_id': 'frobnitz'})
        self.failUnless(document.get('__acl__'), [[1, 2, 3]])

    def test_add_and_remove_ace(self):
        self.request.db['test'].insert({'_id': 'frobnitz', 'title': ''})
        from lumin.node import ContextById

        class AContext(ContextById):
            _default__acl__ = [[1, 2, 3]]

        context = AContext(self.request, 'frobnitz', 'test')
        self.assertEquals(context.__acl__, [[1, 2, 3]])
        context.save()
        document = self.request.db['test'].find_one({'_id': 'frobnitz'})
        self.failUnless(document.get('__acl__'), [[1, 2, 3]])

        context.add_ace(['a', 'b', 'c'])
        self.assertEquals(context.__acl__, [[1, 2, 3], ['a', 'b', 'c']])
        document = self.request.db['test'].find_one({'_id': 'frobnitz'})
        self.failUnless(document.get('__acl__'), [[1, 2, 3], ['a', 'b', 'c']])

        context.remove_ace([1, 2, 3])
        self.assertEquals(context.__acl__, [['a', 'b', 'c']])
        document = self.request.db['test'].find_one({'_id': 'frobnitz'})
        self.failUnless(document.get('__acl__'), [['a', 'b', 'c']])

        context.add_ace(['a', 'b', 'd'])
        self.assertEquals(context.__acl__, [['a', 'b', ['c', 'd']]])

        context.remove_ace(['a', 'b', 'c'])
        self.assertEquals(context.__acl__, [['a', 'b', 'd']])


# class ContextBySpecTestCase(BaseFunctionalTestCase):
#     def test_unique(self):
#         # Insert item directly into collection
#         self.request.db['test'].insert(
#             {'_id': 'frobnitz'}, {'title': 'Frobnitz'}
#             )

#         from lumin.node import ContextBySpec
#         context = ContextBySpec(
#             self.request, {'_id': 'frobnitz'}, 'test', unique=True
#             )
#         self.assertEqual(context.data['_id'], 'frobnitz')

#     def test_not_unique(self):
#         # Insert item directly into collection
#         self.request.db['test'].insert(
#             {'_id': 'frobnitz'}, {'title': 'Frobnitz'}
#             )

#         from lumin.node import ContextBySpec
#         context = ContextBySpec(
#             self.request, {'_id': 'frobnitz'}, 'test', unique=False
#             )
#         self.assertEqual(context.data[0]['_id'], 'frobnitz')
