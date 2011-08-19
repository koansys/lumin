import lumin
import unittest
import pyramid.events
import pyramid.testing


class NodeTestCase(unittest.TestCase):
    def setUp(self):
        self.request = pyramid.testing.DummyRequest()
        self.config = pyramid.testing.setUp(
            request=self.request,
            settings={
                'secret': 'secret',
                'db_name': 'test',
                })

        self.config.include(lumin)
        conn = self.config.register_mongodb('mongodb://localhost/')

        # Drop and create test database
        conn.drop_database('test')
        db = conn['test']

        # Create collections
        db.create_collection('test')

        # Fire new request event to set up environment
        self.config.registry.handle(pyramid.events.NewRequest(self.request))

    def tearDown(self):
        pyramid.testing.tearDown()


class CollectionTestCase(NodeTestCase):
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
            {'_id': 'frobnitz'}, u'Frobnitz')
        self.assertEqual(result, 'frobnitz')

        # Insert another, with "increment" enabled
        result = collection.insert(
            {'_id': 'frobnitz'}, u'Frobnitz', increment=True)
        self.assertEqual(result, 'frobnitz-1')


class ContextByIdTestCase(NodeTestCase):
    def test_save(self):
        # Insert item directly into collection
        self.request.db['test'].insert(
            {'_id': 'frobnitz'}, {'title': u'Frobnitz'}
            )
        from lumin.node import ContextById
        context = ContextById(self.request, 'frobnitz', 'test')
        context.data.update({'title': u'Frobbozz'})
        context.save()
        self.assertRaises(StopIteration, context.history)
        self.assertTrue(context.data['mtime'])

    def test_update(self):
        # Insert item directly into collection
        self.request.db['test'].insert(
            {'_id': 'frobnitz'}, {'title': u'Frobnitz'}
            )

        from lumin.node import ContextById
        context = ContextById(self.request, 'frobnitz', 'test')
        result = context.update({'title': u'Frobbozz'})
        self.assertEqual(result, None)
        self.assertEqual(context.data['title'], u'Frobbozz')

        data = self.request.db['test'].find({'_id': 'frobnitz'}).next()
        self.assertEqual(data['title'], context.data['title'])
        self.assertEqual(data['changed_by'], '')
        self.assertTrue(data['mtime'])

    def test_update_history(self):
        # Insert item directly into collection
        self.request.db['test'].insert({'_id': 'frobnitz', 'title': u''})

        from lumin.node import ContextById
        context = ContextById(self.request, 'frobnitz', 'test')

        # Update 1
        context.update({'title': u'Frobnitz'})

        # Update 2
        context.update({'title': u'Frobbozz'})

        history = context.history()

        self.assertEqual(history.count(), 2)
        obj = history.next()
        self.assertEqual(obj['title'], u'Frobnitz')
        self.assertNotEqual(obj['mtime'], context.data['mtime'])
        self.assertEqual(history.next()['title'], u'')
        self.assertEqual(context.data['title'], u'Frobbozz')



class ContextBySpecTestCase(NodeTestCase):
    def test_unique(self):
        # Insert item directly into collection
        self.request.db['test'].insert(
            {'_id': 'frobnitz'}, {'title': u'Frobnitz'}
            )

        from lumin.node import ContextBySpec
        context = ContextBySpec(
            self.request, {'_id': 'frobnitz'}, 'test', unique=True
            )
        self.assertEqual(context.data['_id'], 'frobnitz')

    def test_not_unique(self):
        # Insert item directly into collection
        self.request.db['test'].insert(
            {'_id': 'frobnitz'}, {'title': u'Frobnitz'}
            )

        from lumin.node import ContextBySpec
        context = ContextBySpec(
            self.request, {'_id': 'frobnitz'}, 'test', unique=False
            )
        self.assertEqual(context.data[0]['_id'], 'frobnitz')
