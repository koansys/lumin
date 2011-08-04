import datetime

from pymongo.errors import DuplicateKeyError

import colander
import deform

from webob.exc import HTTPInternalServerError

from pyramid.exceptions import NotFound
from pyramid.security import Allow
from pyramid.security import Everyone

from lumin.util import TS_FORMAT
from lumin.util import cancel
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

    def update(self):
        """
        Update the item this ``context`` represents in its
        :term:`collection`
        """
        self.data['mtime'] = datetime.datetime.utcnow().strftime(TS_FORMAT)

        result = self._collection.update(
            {"_id": self.data["_id"]},
            self.data,
            manipulate=True,
            safe=True
            )

        return result

    def delete(self, safe=False):
        """
        Remove the entry represented by this ``context`` from this
        :term:`collection`
        """
        result = self._collection.remove(self.data["_id"], safe=safe)
        if safe and result['err']:
            raise result['err']


class ContextById(Collection):
    __acl__ = []  # this should become _default__acl__

    #: the collection name we will use in the DB
    __collection__ = None

    __name__ = __parent__ = None
    __schema__ = colander.Schema

    button_name = "Submit"

    def __init__(self, request, _id=None):
        super(ContextById, self).__init__(request)
        self.request = request
        self.environ = request.environ
        self.data = {}
        ## These next two can prolly use the setters below, maybe...
        ## but this way you can set it as a class variable and then
        ## override it live with another coll/schema and then get the
        ## original back by self.property = self.__property__
        ## This is perhaps desirable for our two schemas one form
        ## dilemma. Use a non-validating (all colander.null) schema
        ## while filling shit out then self.schema = ValidatingSchema
        ## when finalizing and submitting.
        self._schema = self.__schema__().bind(request=self.request)
        self._id = _id if _id else request.matchdict.get('slug')
        if self._id:
            cursor = self._collection.find(
                {'_id': self._id}
                )
            try:
                assert cursor.count() < 2
                self.data = cursor.next()
            except StopIteration:
                raise NotFound
            except AssertionError:
                raise HTTPInternalServerError

    @property
    def __name__(self):
        return self._id

    def add_form(self):
        """
        :rtype: a tuple consisting of the form and and required static resources

        This form is for adding a new that does not yet have a
        :term:`context`. This isn't entirely true. We have generated a
        context here, but is isn't in the DB yet and it has no data
        yet. It is essentially a context shell at this point.
        """
        buttons = (deform.form.Button(name = "submit",
                                      title = self.button_name
                                        ),
                   cancel)
        form = deform.Form(self._schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)

    def edit_form(self):
        """
        :rtype: a tuple consisting of the form and and required static resources.

        This form is for editing an existing item represented by this :term:`context`

        TODO: can these two forms be the same form?
        """
        buttons = (deform.form.Button(name = "submit",
                                      title = "Update"
                                      ),
                   cancel)
        form = deform.Form(self._schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)


class ContextBySpec(Collection):
    """
    Like ContextById but takes a *spec*ifying dictionary instead.

    :param request: A pyramid request object
    :param spec: A dictionary to use to extract the desired item from the DB
    :param unique: Should this context be a single item
    """
    _default__acl__ = __acl__ = []

    #: the collection name we will use in the DB
    __collection__ = None
    __name__ =  __parent__ = None
    __schema__ = colander.Schema
    button_name = "Submit"

    def __init__(self, request, spec=None, unique=True):
        super(ContextBySpec, self).__init__(request)
        self.request = request
        self.environ = request.environ
        self.spec = spec
        self.unique = unique
        self.data = {}
        self._schema = self.__schema__().bind(request=self.request)
        for item in self._default__acl__:
            if item not in self.__acl__:
                self.__acl__.append(item)
        if self.spec:
            cursor = self._collection.find(spec)
            if self.unique:
                try:
                    assert cursor.count() < 2
                    self.data = cursor.next()
                    self._id = self.data['_id']
                except StopIteration:
                    raise NotFound
                except AssertionError:
                    raise HTTPInternalServerError("More than one result "
                                                  + "matched the spec")
        acl = self.data.get('__acl__', None)
        if acl:
            self.__acl__.extend(acl)

    @property
    def __name__(self):
        ## this is probably wrong, but maybe not need to think.
        return self._id

    def add_form(self):
        """
        :rtype: a tuple consisting of the form and and required static resources

        This form is for adding a new that does not yet have a
        :term:`context`. This isn't entirely true. We have generated a
        context here, but is isn't in the DB yet and it has no data
        yet. It is essentially a context shell at this point.
        """
        buttons = (deform.form.Button(name = "submit",
                                      title = self.button_name
                                        ),
                   cancel)
        form = deform.Form(self._schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)

    def edit_form(self):
        """
        :rtype: a tuple consisting of the form and and required static resources.

        This form is for editing an existing item represented by this :term:`context`

        TODO: can these two forms be the same form?
        """
        buttons = (deform.form.Button(name = "submit",
                                      title = "Update"
                                      ),
                   cancel)
        form = deform.Form(self._schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)
