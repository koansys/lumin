import datetime

from pymongo.errors import DuplicateKeyError

import colander
import deform

from webob.exc import HTTPInternalServerError

from pyramid.exceptions import NotFound

from lumin import normalize
from lumin import RootFactory
from lumin.util import cancel
from lumin.util import TS_FORMAT


class NodeById(RootFactory):

    __acl__ = []

    __collection__ = None #'root'
    __name__ =  __parent__ = None
    __schema__ = colander.Schema
    button_name = "Submit"

    def __init__(self, request, _id=None):
        super(NodeById, self).__init__(request)
        self.request = request
        self.environ = request.environ
        self.collection = self.db[self.__collection__]
        self.schema = self.__schema__().bind(request=self.request)
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

    def add_form(self):
        buttons = (deform.form.Button(name = "submit",
                                        title = self.button_name
                                        ),
                   cancel)
        form = deform.Form(self.schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)

    def edit_form(self):
        buttons = (deform.form.Button(name = "submit",
                                      title = "Update"
                                      ),
                   cancel)
        form = deform.Form(self.schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)


    def insert(self, doc, title_or_id, increment=True):
        """
        Insert the item this context represents into the
        :term:`collection`.
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
            oid = self.collection.save(doc, safe=True)
        return oid

    def update(self):
        """
        update the item this ``context`` represents in the
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
        Remove the entry represented by this context from this
        :term:`collection`
        """
        result = self.collection.remove(self.data["_id"],
                                        safe=safe)
        if safe and result['err']:
            raise result['err']

