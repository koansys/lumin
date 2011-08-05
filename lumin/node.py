import datetime

from pymongo.errors import DuplicateKeyError
from webob.exc import HTTPInternalServerError

from pyramid.exceptions import NotFound
from pyramid.security import Allow
from pyramid.security import Everyone

from lumin.util import TS_FORMAT
from lumin.util import normalize


class Factory(object):
    """Pyramid context factory base class."""

    __acl__ = [
            (Allow, Everyone, 'view'),
        ]

    __name__ = __parent__ = None

    def __init__(self, request):
        self.request = request


class Collection(Factory):
    """Represents a collection context."""

    # Database collection name
    collection = None

    def __init__(self, request):
        super(Collection, self).__init__(request)
        self._collection = request.db[self.collection]

    @property
    def __name__(self):
        return self.collection

    def find(self, **kwargs):
        return self._collection.find(**kwargs)

    def insert(self, doc, title_or_id, increment=True, seperator=u'-'):
        """
        Insert ``doc`` into the :term:`collection`.

        :param doc: A dictionary to be stored in the DB
        :param title_or_id: a string to be normalized for a URL and used as the _id for the document.
        :param increment: Whether to increment ``title_or_id`` if it already exists in the DB. **Default: ``True``**
        :param seperator: carachter to separate ``title_or_id`` incremental id. **Default: ``u"-"``**
        """

        ctime = mtime = datetime.datetime.utcnow().strftime(TS_FORMAT)
        doc['ctime'] = ctime
        doc['mtime'] = mtime
        doc['_id'] = normalize(title_or_id)

        if increment:
            suffix = 0
            _id = doc['_id']
            while True:
                try:
                    oid = self._collection.insert(doc, safe=True)
                    break
                except DuplicateKeyError:
                    suffix += 1
                    _id_suffixed = u','.join([_id, unicode(suffix)])
                    doc['_id'] = _id_suffixed
        else:
            oid = self._collection.insert(doc, safe=True)

        return oid

    def delete(self, safe=False):
        """
        Remove the entry represented by this ``context`` from this
        :term:`collection`
        """
        result = self._collection.remove(self.data["_id"], safe=safe)
        if safe and result['err']:
            raise result['err']


class ContextById(Collection):
    def __init__(self, request, _id=None):
        super(ContextById, self).__init__(request)

        # We get the object id from the request slug; the ``_id``
        # keyword argument is just for testing purposes
        self._id = _id if _id is not None else \
                   request.matchdict['slug']

        cursor = self._collection.find({'_id': self._id})
        if cursor.count() > 1:
            raise HTTPInternalServerError(
                "Duplicate object found for '%s'." % self._id
                )

        try:
            self.data = cursor.next()
        except StopIteration:
            raise NotFound(self._id)

    @property
    def __name__(self):
        return self._id

    def save(self):
        return self.update(self.data)

    def update(self, data):
        """
        Update the item this ``context`` represents in its
        :term:`collection`.
        """

        self.data = data
        self.data['mtime'] = datetime.datetime.utcnow().strftime(TS_FORMAT)

        return self._collection.update(
            {"_id": self._id},
            self.data,
            manipulate=True,
            safe=True
            )


class ContextBySpec(Collection):
    """
    Like ContextById but takes a *spec*ifying dictionary instead.

    :param request: A pyramid request object
    :param spec: A dictionary to use to extract the desired item from the DB
    :param unique: Should this context be a single item
    """

    def __init__(self, request, spec=None, unique=True):
        super(ContextBySpec, self).__init__(request)

        cursor = self._collection.find(spec)
        if unique:
            if cursor.count() > 1:
                raise HTTPInternalServerError(
                    "Multiple objects found for specification: '%s'." % \
                    self._id
                    )

            try:
                self.data = cursor.next()
            except StopIteration:
                raise NotFound(spec)
        else:
            self.data = tuple(cursor)
