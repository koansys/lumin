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
    event.request.fs = GridFS(db)


def register_mongodb(config, db_uri, slave_okay=False):
    conn = pymongo.Connection(db_uri, slave_okay=slave_okay)
    config.registry.registerUtility(conn, IMongoDBConnection)
    return conn
