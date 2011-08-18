import datetime
import time

from pymongo.errors import DuplicateKeyError
from webob.exc import HTTPInternalServerError

from pyramid.exceptions import NotFound
from pyramid.security import Allow
from pyramid.security import Everyone
from pyramid.security import authenticated_userid

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

    def __init__(self, request, name=None):
        super(Collection, self).__init__(request)

        name = self.collection = name if name is not None else self.collection
        self._collection = request.db[name]
        self._collection_history = request.db['%s.history' % name]

    @property
    def __name__(self):
        return self.collection

    def find(self, **kwargs):
        return self._collection.find(kwargs)

    def get(self, _id):
        return ContextById(self.request, _id=_id, name=self.collection)

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
                    _id_suffixed = seperator.join([_id, unicode(suffix)])
                    doc['_id'] = _id_suffixed
        else:
            oid = self._collection.insert(doc, safe=True)

        return oid

    def delete(self, _id, safe=False):
        """
        Delete the entry represented by this ``_id`` from this
        :term:`collection`
        """
        result = self._collection.remove(_id, safe=safe)
        if safe and result['err']:
            raise result['err']


class ContextById(Collection):
    def __init__(self, request, _id=None, name=None):
        super(ContextById, self).__init__(request, name=name)

        # We get the object id from the request slug; the ``_id``
        # keyword argument is just for testing purposes
        self._id = _id if _id is not None else \
                   request.matchdict['slug']

        self._spec = {"_id": self._id}

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
    def history(self):
        """
        Return historical versions of this :term:`context`.
        """

        query = self._collection_history.find(self._spec)
        try:
            data = query.next()
        except StopIteration:
            return []
        else:
            return data['versions']

    def remove(self, safe=False):
        """
        Record current data in history and remove the entry
        represented by this :term:`context` from the
        :term:`collection`
        """

        self._record()
        result = self._collection.remove(self._id, safe=safe)
        if safe and result['err']:
            raise result['err']

    def save(self):
        """
        Save current data of this :term:`context`.
        """

        self._touch()

        result = self._collection.update(
            self._spec,
            self.data,
            manipulate=True,
            safe=True
            )

    def update(self, data):
        """
        Record current data in history and update the item this
        :term:`context` represents in its :term:`collection`.
        """

        self._record()
        self.data = data
        self.data['_id'] = self._id
        self.save()

    def _record(self):
        self._touch()
        self._collection_history.update(
            self._spec, {
                '$push': {
                    'versions': self.data,
                    }
                },
            True
            )

    def _touch(self):
        user = authenticated_userid(self.request)
        self.data['mtime'] = datetime.datetime.utcnow().strftime(TS_FORMAT)
        self.data['changed_by'] = user if user is not None else ''


class ContextBySpec(Collection):
    """
    Like ContextById but takes a *spec*ifying dictionary instead.

    :param request: A pyramid request object
    :param spec: A dictionary to use to extract the desired item from the DB
    :param unique: Should this context be a single item
    """

    __name__ = None

    def __init__(self, request, spec=None, name=None, unique=True):
        super(ContextBySpec, self).__init__(request, name=name)

        cursor = self._collection.find(spec)
        if unique:
            if cursor.count() > 1:
                raise HTTPInternalServerError(
                    "Multiple objects found for specification: '%s'." % \
                    spec,
                    )

            try:
                self.data = cursor.next()
            except StopIteration:
                raise NotFound(spec)
        else:
            self.data = tuple(cursor)
