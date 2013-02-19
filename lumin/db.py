from datetime import datetime
from datetime import timedelta

from gridfs import GridFS
import pymongo

from pyramid.url import route_url

from zope.interface import Interface

from pyramid.events import subscriber
from pyramid.interfaces import INewRequest

from lumin.son import ColanderNullTransformer

memcache = None
try:
    import memcache
except ImportError:
    pass


class IMongoDBConnection(Interface):
    pass


def get_mongodb(registry):
    settings = registry.settings
    db_name = settings['db_name']
    db = registry.getUtility(IMongoDBConnection)[db_name]
    db.add_son_manipulator(ColanderNullTransformer())
    return db


@subscriber(INewRequest)
def add_mongodb(event):
    db = get_mongodb(event.request.registry)
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



class MongoUploadTmpStore(object):
    __collection__ = 'tempstore'
    def __init__(self,
                 request,
                 gridfs=None,
                 image_mimetypes=('image/jpeg', 'image/png', 'image/gif'),
                 max_age=3600):
        self.request = request
        self.fs = gridfs if gridfs else GridFS(request.db,
                                               collection=self.__collection__)
        self.tempstore = request.db[self.__collection__]
        self.max_age = timedelta(seconds=max_age)
        ## XXX: Total hackery
        ## TODO: remove when mongo gets TTL capped collections.
        expired = self.tempstore.files.find(
            {'uploadDate' : {"$lt" : datetime.utcnow() - self.max_age}})
        for file_ in expired:
            self.fs.delete(file_['_id'])

    def get(self, uid, default=None):
        result = self.tempstore.files.find_one({'metadata.uid': uid })
        if result is None:
            return default
        oid = result['_id']
        fp  = self.fs.get(oid)
        if fp is None:
            return default
        result['fp'] = fp
        return result

    def __getitem__(self, uid):
        result = self.get(uid)
        if result is None:
            raise KeyError(uid)
        return result

    def __contains__(self, uid):
        return self.get(uid) is not None

    def __setitem__(self, oid, cstruct):
        fp = cstruct.get('fp')
        content_type = cstruct.get('mimetype')
        filename = cstruct.get('filename')
        metadata = {'filename' : cstruct.get('filename'),
                    'mimetype' : cstruct.get('mimetype'),
                    'uid' : cstruct.get('uid'),
            }
        self.fs.put(
            fp,
            content_type=content_type,
            filename=filename,
            metadata=metadata
            )
        fp.seek(0) ## reset so view can read

    def __delitem__(self, uid):
        result = self.tempstore.files.find_one({'metadata.uid': uid })
        oid = result['_id']
        self.fs.delete(oid)


    def preview_url(self, uid):
        return None
        gf = self.get(uid)
        if gf and gf.get('content_type') in self.image_mimetypes:
            return route_url('preview_image', self.request, uid=uid)
        else:
            return None #route_url('preview_image', self.request, uid=uid)
