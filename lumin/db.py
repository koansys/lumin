from datetime import datetime
from datetime import timedelta

from gridfs import GridFS
import pymongo
from pymongo.objectid import ObjectId
from pymongo.errors import InvalidId

from pyramid.url import route_url

from zope.interface import Interface
from zope.component.interfaces import ComponentLookupError

from pyramid.events import subscriber
from pyramid.interfaces import INewRequest
from pyramid.threadlocal import get_current_registry
from pyramid.settings import get_settings




from lumin.son import ColanderNullTransformer

memcache = None
try:
    import memcache
except ImportError:
    pass


class IMongoDBConnection(Interface):
    pass

def get_mongodb():
    settings = get_settings()
    db_name = settings['db_name']
    reg = get_current_registry()
    db = reg.getUtility(IMongoDBConnection)[db_name]
    db.add_son_manipulator(ColanderNullTransformer())
    return db

@subscriber(INewRequest)
def add_mongodb(event):
    db = get_mongodb()
    event.request.db = db
    event.request.fs = GridFS(db)

def register_mongodb(config, db_uri):
    conn = pymongo.Connection(db_uri)
    config.registry.registerUtility(conn, IMongoDBConnection)
    return conn

### XXX DO I really want memcached
class IMemcachedClient(Interface):
    pass

def get_memcached():
    reg = get_current_registry()
    mc = reg.queryUtility(IMemcachedClient)

@subscriber(INewRequest)
def add_memcached(event):
    mc = get_memcached()
    if mc:
        event.request.mc = mc

def register_memchached(config, mc_host):
    mc_conn = memcache.Client(mc_host)
    config.registerUtility(mc_conn, IMemcachedClient)


class MongoFileStore(object):
    def __init__(self, request):
        self.request = request

    def get(self, oid, default=None):
        try:
            result = self.request.get(ObjectId(oid))
        except InvalidId as err:
            return default
        return result

    def __getitem__(self, oid):
        fh = self.get(oid)
        if fh is None:
            raise KeyError(oid)
        return fh

    def __contains__(self, oid):
        return self.request.fs.exists(oid)

    def __setitem__(self, oid, cstruct):
        fp = cstruct.get('fp')
        content_type = cstruct.get('mimetype')
        filename = cstruct.get('filename')
        oid = self.request.fs.put(
            fp,
            content_type=content_type,
            filename=filename,
            metadata=cstruct
            )

    def preview_url(self, oid):
        gf = self.get(oid)
        if gf.get('content_type') in self.image_mimetypes:
            return route_url('preview_image', self.request, oid=oid)
        else:
            return None #route_url('preview_image', self.request, uid=uid)

class MongoUploadTmpStore(object):
    __collection__ = 'tempstore'
    def __init__(self,
                 request,
                 image_mimetypes=('image/jpeg', 'image/png', 'image/gif'),
                 max_age=86400):
        self.request = request
        self.fs = GridFS(request.db, collection=self.__collection__)
        self.max_age = timedelta(seconds=self.max_age)
        ## XXX: Total hackery
        ## TODO: remove when mongo gets TTL capped collections.
        expired = self.request.db[self.__collection__].find(
            {'uploadDate' : {"$lt" : datetime.now() - self.max_age}})
        for file_ in expired:
            self.fs.delete(file_)

    def get(self, oid, default=None):
        try:
            result = self.fs.get(ObjectId(oid))
        except InvalidId as err:
            return default
        return result

    def __getitem__(self, oid):
        fh = self.get(oid)
        if fh is None:
            raise KeyError(oid)
        return fh

    def __contains__(self, oid):
        return self.fs.exists(oid)

    def __setitem__(self, oid, cstruct):
        fp = cstruct.get('fp')
        content_type = cstruct.get('mimetype')
        filename = cstruct.get('filename')
        oid = self.fs.put(
            fp,
            content_type=content_type,
            filename=filename,
            metadata=cstruct
            )

    def preview_url(self, oid):
        gf = self.get(oid)
        if gf.get('content_type') in self.image_mimetypes:
            return route_url('preview_image', self.request, oid=oid)
        else:
            return None #route_url('preview_image', self.request, uid=uid)
