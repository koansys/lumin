from gridfs import GridFS
import pymongo

from zope.interface import Interface

from pyramid.events import subscriber
from pyramid.interfaces import INewRequest

from lumin.son import ColanderNullTransformer


class IMongoDBConnection(Interface):  # pragma: nocover
    pass


def get_mongodb(registry):
    db_name = registry.settings['db_name']
    db = registry.getUtility(IMongoDBConnection)[db_name]
    db.add_son_manipulator(ColanderNullTransformer())
    return db


@subscriber(INewRequest)
def add_mongodb(event):
    db = get_mongodb(event.request.registry)
    event.request.db = db
    try:
        event.request.fs = GridFS(db)
    except TypeError:
        ## TODO: need to find a better way
        ## NB: using mock db so we use a mock gfs
        ## not sure if we can add a mock gfs to the
        ## firing event in
        from lumin.testing import MockGridFS
        event.request.fs = MockGridFS(event.request.db)


def register_mongodb(config, db_uri, slave_okay=False, conn=None):
    conn = conn if conn else pymongo.Connection(db_uri, slave_okay=slave_okay)
    config.registry.registerUtility(conn, IMongoDBConnection)
    return conn
