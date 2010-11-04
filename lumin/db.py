from zope.interface import Interface
from zope.component.interfaces import ComponentLookupError

from repoze.bfg.events import subscriber
from repoze.bfg.interfaces import INewRequest
from repoze.bfg.threadlocal import get_current_registry
from repoze.bfg.settings import get_settings

import pymongo
from gridfs import GridFS

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
