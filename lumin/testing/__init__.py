from __future__ import unicode_literals

import datetime

import mongomock

from bson.objectid import ObjectId


class MockGridOut(dict):
    def __init__(self, obj):
        self.update(obj)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(
            "MockGridOut has no attribute '{}'".format(name))

    def read(self):
        return self['data'].read()


class MockGridFS:
    def __init__(self, db, collection='files'):
        self.conn = mongomock.Connection()
        self.db = db if db else mongomock.Database(self.conn)
        self.collection = self.__dict__[collection if collection else 'fs'] =\
            mongomock.Collection(self.db)
        self.collection.files = mongomock.Collection(self.db)
        self.storage = {}

    def delete(self, oid):
        if oid in self.storage:
            del self.storage[oid]

    def get(self, oid):
        result = doc = self.storage.get(oid, None)
        if doc:
            result = MockGridOut(doc)
        return result

    def list(self):
        return [v['filename'] for (k, v) in self.storage.items()]

    def put(self, data, **kwargs):
        doc = kwargs
        _id = ObjectId()
        doc['_id'] = _id
        doc['length'] = len(data.read())
        doc['uploadDate'] = datetime.datetime.now()
        data.seek(0)
        self.collection.files.insert(doc)
        doc['data'] = data
        self.storage[_id] = doc
        return _id


class Database(mongomock.Database):
    def __init__(self, conn):
        super(Database, self).__init__(conn)

    def __getitem__(self, db_name):
        db = self._collections.get(db_name, None)
        if db is None:
            db = self._collections[db_name] = Collection(self)
        return db

    def __getattr__(self, attr):
        return self[attr]


class Connection(mongomock.Connection):
    def __init__(self):
        super(Connection, self).__init__()

    def __getitem__(self, db_name):
        db = self._databases.get(db_name, None)
        if db is None:
            db = self._databases[db_name] = Database(self)
        return db

    def __getattr__(self, attr):
        return self[attr]


class Collection(mongomock.Collection):
    def __call__(self, *args, **kwargs):
        pass
