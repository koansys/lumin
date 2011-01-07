from datetime import datetime
from datetime import timedelta

import colander
import deform
from deform.i18n import _

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



class MongoUploadTmpStore(object):
    __collection__ = 'tempstore'
    def __init__(self,
                 request,
                 image_mimetypes=('image/jpeg', 'image/png', 'image/gif'),
                 max_age=3600):
        self.request = request
        self.fs = GridFS(request.db, collection=self.__collection__)
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
        fp = cstruct.pop('fp')
        content_type = cstruct.get('mimetype')
        filename = cstruct.get('filename')
        oid = self.fs.put(
            fp,
            content_type=content_type,
            filename=filename,
            metadata=cstruct
            )


    def preview_url(self, uid):
        return None
        gf = self.get(uid)
        if gf and gf.get('content_type') in self.image_mimetypes:
            return route_url('preview_image', self.request, uid=uid)
        else:
            return None #route_url('preview_image', self.request, uid=uid)


class FileData(object):
    def serialize(self, node, value):
        if value is colander.null:
            return colander.null
        for n in ('filename', 'uid'):
            if not n in value:
                mapping = {'value':repr(value), 'key':n}
                raise colander.Invalid(
                    node,
                    _('${value} has no ${key} key', mapping=mapping)
                    )
        result = deform.widget.filedict()
        result['filename'] = value['filename']
        result['uid'] = value['uid']
        result['mimetype'] = value.get('mimetype')
        result['size'] = value.get('size')
        file_id = result.get('file_id')
        if file_id is not None:
            result['fp'] = node.fs.get(file_id)
        else:
            result['fp'] = None
        result['preview_url'] = value.get('preview_url')
        return result

    def deserialize(self, node, value):
        if value is colander.null:
            return colander.null
        #fp = value['fp']
        #del value['fp'] # pickleability
#        import StringIO
#        fp = StringIO.StringIO("Hello world\n")
#        fs = node.fs
#        fp.seek(0)
#        file_id = fs.put( # XXX this is broken
#            fp,
#            content_type=value['mimetype'],
#            filename=value['filename'],
#           metadata=value
#            )
#        value['file_id'] = file_id
        return value

