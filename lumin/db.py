from gridfs import GridFS
import pymongo

from zope.interface import Interface

from pyramid.events import subscriber
from pyramid.interfaces import INewRequest

from lumin.son import ColanderNullTransformer


class IMongoDBConnection(Interface):  # pragma: nocover
    pass


def get_mongodb(registry):

    db_name = registry.settings['mongodb.db_name']
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


def connection_from_settings(settings):
    """
    :param settings: a `pyramid.config.Configurator.registry.settings`
    instance. It should contain a client class to use for the connection as
    mongodb.client_class and a connection string as a uri as mongodb.db_uri
    appropriate client class options for the `mongodb.client_class` specified
    or the `pymongo.mongo_client.MongoClient <http://bit.ly/YK37OJ>`_
    class by default. I.e. see `pymongo.mongo_client.MongoClient <http://bit.ly/YK37OJ>`_
    for a list of options appropriate to
    `pymongo.mongo_client.MongoClient <http://bit.ly/YK37OJ>`
    """
    mongo_options = {k.split("mongodb.options.")[-1]: v for k, v in \
        settings.items() if k.startswith('mongodb.options.')}
    connclass = getattr(pymongo,
        settings.get("mongodb.connection_class", "MongoClient"))
    return connclass(settings.get('mongodb.db_uri'), **mongo_options)


def register_mongodb(config, conn=None):
    """
    Register a mongodb connection with the configuration registry.
    This is added as a `pyramid.config.Configurator <http://bit.ly/QNns19>`_
    durective in :meth:`lumin.includeme`. Then a database connection can be
    created and registered in the `pyramid.config.Configurator <http://bit.ly/QNns19>`_
    during application startup.

    .. code-block:: python

        config = Configurator(...)
        ...
        conn = pymongo.MongoClient(...)
        config.register_mongodb(conn=conn)

    Alternatively you can pass nothing and lumin will attempt to create a
    connection from the `pyramid.config.Configurator <http://bit.ly/QNns19>`_
    `pyramid.registry.Registry.settings <http://bit.ly/QNrUNp>`_. See
    :meth:`lumin.db.connection_from_settings` for more details.

    .. code-block:: python

        config = Configurator(...)
        config = config.register_mongodb()
    """

    conn = connection_from_settings(config.registry.settings)
    config.registry.registerUtility(conn, IMongoDBConnection)
    return conn
