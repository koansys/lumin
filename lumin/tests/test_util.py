# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import unittest
from pyramid import testing


class TestTestUtil(unittest.TestCase):
    def make_one(self, title="testing title"):
        from lumin.util import normalize
        return normalize(title)

    def test_normalize_lowercases(self):
        result = self.make_one("ABCDE") #testing for lowercase failing
        self.assertTrue(result.islower())
        self.failUnless(result == "abcde")

    def test_normalize_spaces(self):
        result = self.make_one("hj vQ") # testing for spaces in the URI
        self.assertTrue(result == "hj-vq")

    def test_normalize_multiple_spaces(self):
        result = self.make_one("ab  CD  ef") #testing for multiple spaces
        self.assertTrue(result == "ab-cd-ef")

    def test_normalize_remove_unicode(self):
        result = self.make_one("a स्वक्ष z")
        self.assertTrue(result == "a-z")

    def test_normalize_remove_specialChar(self):
        result = self.make_one("a ?/>[)^Ś%$#@ z")
        self.assertTrue(result == "a-z")


class MongoUploadTmpStore(unittest.TestCase):
    def setUp(self):
        config = testing.setUp()
        self.config = config

    def tearDown(self):
        self.config.end()

    def _makeOne(self, request):
        from lumin.grid_fs import MongoUploadTmpStore
        return MongoUploadTmpStore(request, gridfs=request.fs)

    def _makeRequest(self, db, fs):
        from pyramid.testing import DummyRequest
        request = DummyRequest()
        request.db = db
        request.fs = fs
        return request


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

    def find(self, vlaue):
        return []

    def update(self, spec, to_store, **kw):
        self.spec = spec
        self.to_store = to_store
        self.kw = kw

    @property
    def files(self):
        return self


class Database(dict):
    pass

class DummyDB(Database):
    def __init__(self, find_result=None):
        self['tempstore'] = DummyCollection(find_result=find_result)
        dict.__init__(self)

class DummyFS(dict):
    def __init__(self, put_result=None):
        self.put_result = put_result
        dict.__init__(self)

    def put(self, fp, **kw):
        self.fp = fp
        self.kw = kw
        return self.put_result

    def delete(self, _id):
        pass
