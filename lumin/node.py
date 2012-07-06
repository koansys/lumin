from __future__ import unicode_literals

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
              [Allow, Everyone, 'view'],
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

    def insert(self, doc, title_or_id, increment=True, seperator='-'):
        """
        Insert ``doc`` into the :term:`collection`.

        :param doc: A dictionary to be stored in the DB

        :param title_or_id: a string to be normalized for a URL and used as
        the _id for the document.

        :param increment: Whether to increment ``title_or_id`` if it
        already exists in the DB.
        **Default: ``True``**

        :param seperator: character to separate ``title_or_id`` incremental id.
        **Default: ```"-"``**
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
                    _id_suffixed = seperator.join([_id, str(suffix)])
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

        # No return value for "unsafe" request
        if not safe:
            return

        if result['err']:
            raise result['err']

        return bool(result['n'])

    def save(self, to_save, manipulate=True, safe=False):
        """
        Exposes the native pymongo save method
        """
        self._collection.save(to_save, manipulate, safe)


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
                data = next(cursor)
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

    def _acl_apply(self, ace, mutator):
        if not isinstance(ace, list):
            raise TypeError(
                "{} is not a list, mongo stores tuples as a list."
                "Please use lists".format(ace))

        acl = self.__acl__

        if not acl:
            self.__acl__ = [ace]
            return

        a, p, perms = ace

        assert not isinstance(perms, tuple)
        if not isinstance(perms, list):
            perms = (perms, )

        perms = set(perms)

        for i, (action, principal, permissions) in enumerate(acl):
            if a == action and p == principal:
                if not isinstance(permissions, list):
                    permissions = (permissions, )

                permissions = set(permissions)

                # Note that set arguments are updated in place
                mutator(permissions, perms)

                # Set updated permissions as a sorted list
                acl[i][-1] = self._acl_sorted(permissions)

                # Stop when we've applied all permissions
                if not perms:
                    break
        else:
            if perms:
                value = self._acl_sorted(perms)
                acl.append([a, p, value])

        # Filter out trivial entries
        #acl[:] = [a_p_permissions for a_p_permissions in acl if a_p_permissions[2] if isinstance(a_p_permissions[2], list) else True]
        ## PY3: ^ 2to3 suggested to replace lambda below
        acl[:] = filter(
            lambda (a, p, permissions): \
            permissions if isinstance(permissions, list) else True,
            acl
            )

    def _acl_add(self, existing, added):
        existing |= added
        added.clear()

    def _acl_remove(self, existing, added):
        intersection = existing & added

        existing -= intersection
        added -= intersection

    def _acl_sorted(self, permissions):
        if len(permissions) == 1:
            for permission in permissions:
                return permission
        else:
            return list(sorted(permissions))

    def add_ace(self, ace):
        self._acl_apply(ace, self._acl_add)

    def remove_ace(self, ace):
        self._acl_apply(ace, self._acl_remove)

    @property
    def __name__(self):
        return self._id

    @property
    def oid(self):
        return self.data.get('_id', None)

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
        self.data['deleted'] = True
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
    :param _id: An _id to use in a specifying dictionary
    :param name: A collection name
    :param data: Allows construction from dict
    :param unique: Should this context be a single item
    which represent the slug in the url
    """
    _default__acl__ = []

    def __init__(self,
                 request,
                 _id=None,
                 name=None, ## NB: collection name
                 data=None,
                 spec={}):

        super(ContextBySpec, self).__init__(request, name)
        ## We can't limit to one or the other. Currently resource in
        ## cam sends both. Saddly this is horribly broken, yet
        ## works. One Fine day we will refactor this and cam and make
        ## it make more sense. For now no time. I really hate this no
        ## time shit.
        # if _id and spec:
        #     raise AssertionError("provide either an _id or a spec not both")
        self._spec = spec
        if _id:
            ## If we get an ID use it instad od the multi key spec
            ## TODO: Should we enforce ObjectId instance?
            ## This should probably be enforced as bson.oid
            ## See the note in this if's else clause.
            self._spec = {'_id': _id}
        if self._spec and data is None:
            ## If we have a spec let's look for it in the db
            cursor = self._collection.find(self._spec)
            if cursor.count() > 1:
                raise HTTPInternalServerError(
                    "Multiple objects found for specification: '%s'." % \
                    self._spec,
            )
            try:
                ## set data to teh document found
                self.data = next(cursor)
            except StopIteration:
                ## or it doesn't exist
                raise NotFound(repr(self._spec))
        else:
            ## if we didn't have an _id or spec
            ## let's assign data and update
            ## the spec to the doc _id
            self.data = data if data else {}
            ## If there is a real object set the actual id to the doc
            ## _id which would not be the same as the spec.  currently
            ## and wrongly the _id is usually set to the __name__
            ## which wouldn't be correct. The spec oid would never be
            ## the _id in COntextBySpecor we should be using
            ## contextById instead...This assignment sets the _id to
            ## be the bson.ObjectId rahter than the spec. The bson.oid
            ## always is indexed and optimized. Where as a spec may
            ## not be... it isn't really a ghost assingnment.
            ## update and other methods rely on this pointin at the
            ## oid _id not the spec...  We really neeed to refactor
            ## this stuff and make it sane...
            self._spec['_id'] = self.oid
        ## make a copy of the dat for history tracking
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
        if not isinstance(ace, list):
            raise TypeError(
                "{} is not a list, mongo stores tuples as a list."
                "Please use lists".format(ace))
        if not '__acl__' in self.data:
            self.data['__acl__'] = [ace]
        elif ace not in self.__acl__:
            self.data['__acl__'].append(ace)

    def remove_ace(self, ace):
        if not isinstance(ace, list):
            raise TypeError(
                "{} is not a list, mongo stores tuples as a list."
                "Please use lists".format(ace))
        if ace in self.__acl__:
            self.data['__acl__'].remove(ace)

    def get___name__(self):
        return self.data.get('__name__', None)

    def set___name__(self, slug):
        self.data['__name__'] = slug

    __name__ = property(get___name__, set___name__)

    @property
    def oid(self):
        return self.data.get('_id', None)

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
        query = {'orig_id': self.data['_id']}
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

    def insert(self, doc, title_or_id, increment=True, seperator='-'):
        """
        Insert ``doc`` into the :term:`collection`.

        :param doc: A dictionary to be stored in the DB

        :param title_or_id: a string to be normalized for a URL and used as
        the __name__ for the document.

        :param increment: Whether to increment ``title_or_id`` if it
        already exists in the DB.
        **Default: ``True``**

        :param seperator: character to separate ``title_or_id`` incremental id.
        **Default: ```"-"``**
        """

        ctime = mtime = datetime.datetime.utcnow().strftime(TS_FORMAT)
        doc['ctime'] = ctime
        doc['mtime'] = mtime
        doc['__name__'] = normalize(title_or_id)
        if increment:
            suffix = 0
            _id = doc['__name__']
            while True:
                try:
                    self._collection.insert(doc, safe=True)
                    break
                except DuplicateKeyError as e:
                    suffix += 1
                    __name___suffixed = seperator.join([_id, str(suffix)])
                    doc['__name__'] = __name___suffixed
        else:
            self._collection.insert(doc, safe=True)

        return {key: val for key, val in doc.items() if key in self._spec}

    def remove(self, safe=False):
        """
        Record current data in history and remove the entry
        represented by this :term:`context` from the
        :term:`collection`
        """

        self._record()
        result = self._collection.remove(self.oid, safe=safe)
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
