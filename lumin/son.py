from decimal import Decimal

from pymongo.son_manipulator import SONManipulator

import colander

SENTINEL = {u'_type': u'colander.null'}

class ColanderNullTransformer(SONManipulator):
    """
    Added to the db after connection is created. This allows MongoDB to store and
    retrieve sentinals for ``colander.null`` values. ``colander.null``
    is a object which represents that a colander.Schema value is
    missing or undefined. A :term:`son_manipulator` is a object that
    edits :term:`SON` objects as they enter or exit a MongoDB

    .. code-block:: python

       import pymongo
       db = pymongo.Connection().testdb['acollection']
       from lumin.son import ColanderNullTransformer
       db.add_son_manipulator(ColanderNullTransformer())
    """
    def transform_incoming(self, son, collection):
        """
        recursively sets any value that is ``colander.null`` to a
        serializable sentinel value.
        """
        for (k, v) in son.items():
            if v is colander.null:
                son[k] = SENTINEL
                continue
            if isinstance(v, dict):
                self._recursive_in(v)
        return son

    def transform_outgoing(self, son, collection):
        """
        recursively sets any value that is a a
        serialized sentinel value to ``colander.null``.
        """
        for (k, v) in son.items():
            if isinstance(v, dict):
                if v !=SENTINEL:
                    self._recursive_out(v)
                elif v == SENTINEL:
                    son[k] = colander.null
        return son

    def _recursive_in(self, subson):
        """
        called by transform_incoming to provide recursive transformation
        """
        for (k, v) in subson.items():
            if v is colander.null:
                subson[k] = SENTINEL
                continue
            if isinstance(v, dict):
                for (key, value) in v.items():
                    if value is colander.null:
                        v[key] = SENTINEL
                    if isinstance(value, dict):
                        self._recursive_in(value)

    def _recursive_out(self, subson):
        """
        called by transform_outgoing to provide recursive transformation
        """
        for (k, v) in subson.items():
            if isinstance(v, dict):
                if v == SENTINEL:
                    subson[k] = colander.null
                self._recursive_out(v)


class DecimalTransformer(SONManipulator):
    """
    Added to the db after connection is created. This allows MongoDB
    to store and retrieve Decimal values. A :term:`son_manipulator` is
    a object that edits :term:`SON` objects as they enter or exit a
    MongoDB

    .. code-block:: python

       import pymongo
       db = pymongo.Connection().testdb['acollection']
       from lumin.son import DecimalTransformer
       db.add_son_manipulator(DecimalTransformer())

    """
    def transform_incoming(self, son, collection):
        """
        sets any DecimalTransformer to a serializable value.
        """
        for (k, v) in son.items():
            if isinstance(v, Decimal):
                son[k] = {'_type' : 'decimal', 'value' : unicode(v)}
            elif isinstance(v, dict):
                son[k] = self.transform_incoming(v, collection)
        return son

    def transform_outgoing(self, son, collection):
        """
        Sets any top level serialized Decimal to a Decimal. This is
        not recursive.
        """
        for (k, v) in son.items():
            if isinstance(v, dict):
                if "_type" in v and v["_type"] == "decimal":
                   son[k] = Decimal(v['value'])
                else:
                   son[k] = self.transform_outgoing(v, collection)
        return son


class DeNull:
    """
    ``DeNull`` is a callable that recursively replaces
    :term:`colander.null` with an empty ``string`` ``u''``. It is
    usefull for allowing items where :term:`colander.null` is not
    supported.

    .. code-block:: python

       from lumin.son import denull
       foo = desentinel({u"foo" : colander.null})
       assert foo == {u"foo" : u''}
    """
    def __call__(self, son):
        return self._transform(son)

    def _transform(self, son):
        for (k, v) in son.items():
            if v is colander.null:
                son[k] = u''
                continue
            if isinstance(v, dict):
                self._recurse(v)
        return son

    def _recurse(self, subson):
        for (k, v) in subson.items():
            if v is colander.null:
                subson[k] = ''
                continue
            if isinstance(v, dict):
                for (key, value) in v.items():
                    if value is colander.null:
                        v[key] = u''
                    if isinstance(value, dict):
                        self._recurse(value)
denull = DeNull()


class DeSentinel:
    """
    ``DeSentinel`` is similar to ``DeNull``. It is a callable that
    recursively replaces ``lumin.son.SENTINAL`` with an empty
    ``string`` ``u''``. It is usefull to allow using items where
    ``lumin.son.SENTINAL`` is not supported or useful, such as a text
    index.

    .. code-block:: python

       from lumin.son import desentinel
       foo = desentinel({u"foo" : SENTINEL})
       assert foo == {u"foo" : u''}
    """
    def __call__(self, son):
        return self._transform(son)

    def _transform(self, son):
        """
        """
        for (k, v) in son.items():
            if v is SENTINEL:
                son[k] = ''
                continue
            if isinstance(v, dict):
                self._recurse(v)
        return son

    def _recurse(self, subson):
        for (k, v) in subson.items():
            if v is SENTINEL:
                subson[k] = ''
                continue
            if isinstance(v, dict):
                for (key, value) in v.items():
                    if value is SENTINEL:
                        v[key] = ''
                    if isinstance(value, dict):
                        self._recurse(value)
desentinel = DeSentinel()

