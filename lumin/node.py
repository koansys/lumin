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


class RootFactory(object):
    __acl__ = [ (Allow, Everyone, 'view'),]
    __name__ = __parent__ = None
    __collection__ = None
    def __init__(self, request, collection=None):
        self.db = request.db
        self.fs = request.fs
        if request.get('mc', None):
            self.mc = request.mc


class ContextById(RootFactory):

    __acl__ = [] ## this should become _default__acl__

    #: the collection name we will use in the DB
    __collection__ = None #'root'
    __name__ =  __parent__ = None
    __schema__ = colander.Schema
    button_name = "Submit"

    def __init__(self, request, _id=None):
        super(ContextById, self).__init__(request)
        self.request = request
        self.environ = request.environ
        self.data={}
        ## These next two can prolly use the setters below, maybe...
        ## but this way you can set it as a class variable and then
        ## override it live with another coll/schema and then get the
        ## original back by self.property = self.__property__
        ## This is perhaps desirable for our two schemas one form
        ## dilemma. Use a non-validating (all colander.null) schema
        ## while filling shit out then self.schema = ValidatingSchema
        ## when finalizing and submitting.
        self._collection = self.db[self.__collection__]
        self._schema = self.__schema__().bind(request=self.request)
        self._id = _id if _id else request.matchdict.get('slug')
        if self._id:
            cursor = self.collection.find(
                {'_id' : self._id}
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

    @property
    def collection(self):
        """
        returns the :term:`context` factory's :term:`collection` name
        """
        return self._collection

    @collection.setter
    def collection(self, coll):
        """
        sets the context factory's collection

        :param coll: The :term:`collection` name as ``unicode``, ``str``
        """
        if not isinstance(coll, (unicode, str)):
            raise TypeError("{} is not unicode, str")
        self._collection = self.db[coll]

    @property
    def schema(self):
        """
        returns the context factory's schema
        """
        return self._schema

    @schema.setter
    def schema(self, schema, bind=True):
        """
        sets the context factory's schema

        :param schema: an instance of ``colander.MappingSchema``
        :param bind: whether the request should be bound to the
        schema, defaults to True. This is necessary for
        colander.deferred to work with the db which is attached to the
        request.
        """
        if not issubclass(schema, colander.Schema):
            raise TypeError("{} is not a colander.MappingSchema")
        if bind:
            self._schema = schema().bind(request=self.request)
        else:
            self._schema = schema()



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
        form = deform.Form(self.schema, buttons=buttons)
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
        form = deform.Form(self.schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)


    def insert(self,
               doc,
               title_or_id,
               increment=True,
               seperator=u'-'):
        """
        Insert the item this ``context`` represents into the
        :term:`collection`.

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
            suffix=0
            _id = doc['_id']
            while True:
                try:
                    oid=self.collection.insert(doc, safe=True)
                    break
                except DuplicateKeyError as e:
                    suffix+=1
                    _id_suffixed = u','.join([_id, unicode(suffix)])
                    doc['_id'] = _id_suffixed
        else:
            oid = self.collection.insert(doc, safe=True)
        return oid

    def update(self):
        """
        Update the item this ``context`` represents in its
        :term:`collection`
        """
        self.data['mtime'] = datetime.datetime.utcnow().strftime(TS_FORMAT)
        result = self.collection.update({"_id" : self.data["_id"] },
                                        self.data,
                                        manipulate=True,
                                        safe=True)
        return result

    def delete(self, safe=False):
        """
        Remove the entry represented by this ``context`` from this
        :term:`collection`
        """
        result = self.collection.remove(self.data["_id"],
                                        safe=safe)
        if safe and result['err']:
            raise result['err']

class ContextBySpec(RootFactory):
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
        self.data={}
        self._collection = self.db[self.__collection__]
        self._schema = self.__schema__().bind(request=self.request)
        self.__acl__.extend(self._default__acl__)
        if self.spec:
            cursor = self.collection.find(spec)
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

    @property
    def collection(self):
        """
        returns the :term:`context` factory's :term:`collection` name
        """
        return self._collection

    @collection.setter
    def collection(self, coll):
        """
        sets the context factory's collection

        :param coll: The :term:`collection` name as ``unicode``, ``str``
        """
        if not isinstance(coll, (unicode, str)):
            raise TypeError("{} is not unicode, str")
        self._collection = self.db[coll]

    @property
    def schema(self):
        """
        returns the context factory's schema
        """
        return self._schema

    @schema.setter
    def schema(self, schema, bind=True):
        """
        sets the context factory's schema

        :param schema: an instance of ``colander.MappingSchema``
        :param bind: whether the request should be bound to the
        schema, defaults to True. This is necessary for
        colander.deferred to work with the db which is attached to the
        request.
        """
        if not issubclass(schema, colander.Schema):
            raise TypeError("{} is not a colander.MappingSchema")
        if bind:
            self._schema = schema().bind(request=self.request)
        else:
            self._schema = schema()



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
        form = deform.Form(self.schema, buttons=buttons)
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
        form = deform.Form(self.schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)


    def insert(self, doc):
        """
        Insert the item this ``context`` represents into the
        :term:`collection`.  It generates the _id since we don't want
        to ask for docs by this attribute.  The OID is returned.

        :param doc: A dictionary to be stored in the DB
        """
        ctime = mtime = datetime.datetime.utcnow().strftime(TS_FORMAT)
        doc['ctime'] = ctime
        doc['mtime'] = mtime
        oid = self.collection.insert(doc, safe=True)
        return oid

    def update(self):
        """
        Update the item this ``context`` represents in its
        :term:`collection`
        """
        self.data['mtime'] = datetime.datetime.utcnow().strftime(TS_FORMAT)
        oid = self.collection.update({"_id" : self.data["_id"] },
                                     self.data,
                                     manipulate=True,
                                     safe=True)
        return oid

    def delete(self, safe=False):
        """
        Remove the entry represented by this ``context`` from this
        :term:`collection`
        """
        result = self.collection.remove(self.data["_id"],
                                        safe=safe)
        if safe and result['err']:
            raise result['err']
