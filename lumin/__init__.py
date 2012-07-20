# from .db import register_memcached
from lumin.db import register_mongodb

def includeme(config):
    """ Function meant to be included via
    :meth:`pyramid.config.Configurator.include`, which sets up the
    Configurator with a ``register_path`` method."""

    config.add_directive('register_mongodb',
                         register_mongodb,
                         action_wrap=True)
    # config.add_directive('register_memcached',
    #                      register_memcached,
    #                      action_wrap=True)
    config.scan('lumin')
