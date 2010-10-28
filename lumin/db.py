from zope.interface import Interface

from repoze.bfg.events import subscriber
from repoze.bfg.interfaces import INewRequest
from repoze.bfg.threadlocal import get_current_registry
from repoze.bfg.settings import get_settings

import pymongo
from gridfs import GridFS

from lumin.son import ColanderNullTransformer

class IMongoDBConnection(Interface):
    pass

def get_mongodb():
    settings = get_settings()
    db_name = settings['db_name']
    reg = get_current_registry()
    db = reg.getUtility(IMongoDBConnection)[db_name]
    db.add_son_manipulator(ColanderNullTransformer())

@subscriber(INewRequest)
def add_mongodb(event):
    db = get_mongodb()
    event.request.db = db
    event.request.fs = GridFS(db)

def register_mongodb(config, db_uri):
    conn = pymongo.Connection(db_uri)
    config.registry.registerUtility(conn, IMongoDBConnection)
    return conn
