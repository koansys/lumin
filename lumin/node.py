import copy
import datetime

from bson.objectid import ObjectId

from pymongo import DESCENDING
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

    _default__acl__ = __acl__ = [
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

        :param title_or_id: a string to be normalized for a URL and used as
        the _id for the document.

        :param increment: Whether to increment ``title_or_id`` if it
        already exists in the DB.
        **Default: ``True``**

        :param seperator: character to separate ``title_or_id`` incremental id.
        **Default: ``u"-"``**
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

    def save(self, to_save, manipulate=True, safe=False, **kwargs):
        """
        Exposes the native pymongo save method
        """
        self._collection.save(to_save, manipulate, safe, kwargs)


class ContextById(Collection):

    _default__acl__ = []

    def __init__(self, request, _id=None, name=None, data=None):
        super(ContextById, self).__init__(request, name=name)

        # We get the object id from the request slug; the ``_id``
        # keyword argument is just for testing purposes
        self._id = _id if _id is not None else \
                   request.matchdict.get('slug', None)

        self._spec = {"_id": self._id}

        if self._id and data is None:
            try:
                cursor = self._collection.find({'_id': self._id})
                if cursor.count() > 1:
                    raise HTTPInternalServerError(
                        "Duplicate object found for '%s'." % self._id
                        )
                data = cursor.next()
            except StopIteration:
                raise NotFound(self._id)

        self.data = data if data else {}
        self.orig = copy.deepcopy(self.data)
        for ace in self._default__acl__:
            if ace not in self.__acl__:
                self.add_ace(ace)

    def get__acl__(self):
        return self.data.get('__acl__', [])

    def set__acl__(self, acl):
        self.data['__acl__'] = acl

    def delete__acl__(self):
        del self.data['__acl__']

    __acl__ = property(get__acl__, set__acl__, delete__acl__)

    def add_ace(self, ace):
        if not self.__acl__:
            self.data['__acl__'] = [ace]
        elif ace not in self.__acl__:
            self.data['__acl__'].append(ace)

    def remove_ace(self, ace):
        if ace in self.__acl__:
            self.data['__acl__'].remove(ace)

    @property
    def __name__(self):
        return self._id

    def history(self,
                after=True,
                fields=[],
                limit=10,
                since=None,
                sort=DESCENDING):
        """
        Return historical versions of this :term:`context`.

        :param after: if since is provided, only return history items
        after `since`. False will return items before
        since. **Default: ``True``**
        :params fields: a ``list`` or ``dict`` of fields to return in
        the results. If a list it should be list of strings
        representing the fields to return i.e. ``['mtime', ]``. If a
        ``dict`` it should specify either fields to omit or include
        i.e.: ``{'_id': False}`` or {'_id': False, 'title': True,
        'changed_by': True}.
        :param limit: The number of history records to fetch. **Default: 10**
        :param since: a :mod:``datetime.datetime`` object representing
        the date to use as a search point with ``after``. **Default: None**
        :param sort: The direction to sort the history
        items. ``DESCENDING`` provides the most recent change
        first. **Default: ``DESCENDING``**
                """
        if limit is None:
            limit = 0
        if not isinstance(limit, int):
            raise TypeError("expected int, recieved {}".format(type(limit)))
        query = {'orig_id': self._id}
        if since and isinstance(since, datetime.datetime):
            stamp = ObjectId.from_datetime(since)
            if after:
                operator = "$gt"
            else:
                operator = "$lt"
            query['_id'] = {operator: stamp}
        if fields:
            cursor = self._collection_history.find(
                query, fields).limit(limit).sort('_id', DESCENDING)
        else:
            cursor = self._collection_history.find(
                query).limit(limit).sort('_id', DESCENDING)
        return cursor

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
            safe=True)
        if result["updatedExisting"] is False:
            raise KeyError("Update failed: Document not found %r" % self._spec)

    def update(self, data):
        """
        Record current data in history and update the item this
        :term:`context` represents in its :term:`collection`.
        """
        self._record()
        self.data.update(data)
        self.orig = copy.deepcopy(self.data)
        self.save()

    def _record(self):
        self._touch()
        self.orig['orig_id'] = self.data['_id']
        del self.orig['_id']
        self._collection_history.save(
            self.orig,
            manipulate=True,
            safe=True
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
