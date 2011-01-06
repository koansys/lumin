import unittest
from pyramid import testing

class TestMongoFileStore(unittest.TestCase):
    def setUp(self):
        config = testing.setUp()
        self.config = config

    def tearDown(self):
        self.config.end()

    def _makeOne(self, request):
        from gd2.util import MongoFileStore
        return MongoFileStore(request)

    def _makeRequest(self, db, fs):
        from pyramid.testing import DummyRequest
        request = DummyRequest()
        request.db = db
        request.fs = fs
        return request

    def test_get_miss_explicit_default(self):
        db = DummyDB(None)
        fs = DummyFS()
        request = self._makeRequest(db, fs)
        inst = self._makeOne(request)
        default = object()
        result = inst.get('uid', default)
        self.assertEqual(result, default)

    def test_get_miss_implicit_default(self):
        db = DummyDB(None)
        fs = DummyFS()
        request = self._makeRequest(db, fs)
        inst = self._makeOne(request)
        result = inst.get('uid')
        self.assertEqual(result, None)

    def test_get_no_image(self):
        db = DummyDB({'image_id':'abc'})
        fs = DummyFS()
        default = object()
        request = self._makeRequest(db, fs)
        inst = self._makeOne(request)
        result = inst.get('uid', default)
        self.assertEqual(result, default)

    def test_get_with_image(self):
        db = DummyDB({'image_id':'abc'})
        fs = DummyFS()
        fs['abc'] = 'fp'
        default = object()
        request = self._makeRequest(db, fs)
        inst = self._makeOne(request)
        result = inst.get('uid', default)
        self.assertEqual(result, {'fp': 'fp', 'image_id': 'abc'})

    def test___getitem__miss(self):
        db = DummyDB(None)
        fs = DummyFS()
        request = self._makeRequest(db, fs)
        inst = self._makeOne(request)
        self.assertRaises(KeyError, inst.__getitem__, 'uid')

    def test___getitem__hit(self):
        db = DummyDB({'image_id':'abc'})
        fs = DummyFS()
        fs['abc'] = 'fp'
        request = self._makeRequest(db, fs)
        inst = self._makeOne(request)
        self.assertEqual(inst['uid'], {'fp': 'fp', 'image_id': 'abc'})

    def test___contains__hit(self):
        db = DummyDB({'image_id':'abc'})
        fs = DummyFS()
        fs['abc'] = 'fp'
        request = self._makeRequest(db, fs)
        inst = self._makeOne(request)
        self.assertEqual(inst.__contains__('uid'), True)

    def test___contains__miss(self):
        db = DummyDB(None)
        fs = DummyFS()
        request = self._makeRequest(db, fs)
        inst = self._makeOne(request)
        self.assertEqual(inst.__contains__('uid'), False)

    def test___setitem__(self):
        cstruct = {'fp':'fp',
                   'mimetype':'mimetype',
                   'filename':'filename',
                   'size':'size',
                   'uid':'uid'}
        db = DummyDB()
        image_id = 'image_id'
        fs = DummyFS(image_id)
        request = self._makeRequest(db, fs)
        inst = self._makeOne(request)
        inst['uid'] = cstruct
        self.assertEqual(db['tmpstore'].spec, {'uid':'uid'})
        self.assertEqual(db['tmpstore'].to_store,
                         {'mimetype': 'mimetype', 'image_id': 'image_id',
                          'size': 'size', 'uid': 'uid', 'filename': 'filename'})
        self.assertEqual(db['tmpstore'].kw, {'safe': True, 'upsert': True})


class DummyLogger(object):
    def __init__(self):
        self.msgs = []

    def info(self, msg):
        self.msgs.append(msg)

class DummyCollection(object):
    def __init__(self, find_result):
        self.find_result = find_result

    def find_one(self, params):
        return self.find_result

    def update(self, spec, to_store, **kw):
        self.spec = spec
        self.to_store = to_store
        self.kw = kw

class DummyDB(dict):
    def __init__(self, find_result=None):
        self['tmpstore'] = DummyCollection(find_result=find_result)
        dict.__init__(self)

class DummyFS(dict):
    def __init__(self, put_result=None):
        self.put_result = put_result
        dict.__init__(self)

    def put(self, fp, **kw):
        self.fp = fp
        self.kw = kw
        return self.put_result
