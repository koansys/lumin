import datetime

import colander
import deform

from webob.exc import HTTPInternalServerError

from pyramid.exceptions import NotFound
from pyramid.security import Allow
from pyramid.security import Everyone

from lumin import RootFactory
from lumin.util import reset
from lumin.util import TS_FORMAT

class Node(RootFactory):

    __acl__ = []

    __collection__ = None #'root'
    __parent__ = None
    __schema__ = colander.Schema
    button_name = "Submit"
    
    def __init__(self, request):
        super(Node, self).__init__(request)
        self.request = request
        self.environ = request.environ
        self.collection = self.db[self.__collection__]
        self.schema = self.__schema__().bind(request=self.request)
        self._id = request.matchdict.get('slug')
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
                   reset)
        form = deform.Form(self.schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)

    def edit_form(self):
        buttons = (deform.form.Button(name = "submit",
                                        title = "Update"
                                        ),
                   reset)
        form = deform.Form(self.schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)

    def insert(self, doc):
        ctime = atime = datetime.datetime.utcnow().strftime(TS_FORMAT)
        doc['ctime'] = ctime
        doc['atime'] = atime
        oid = self.collection.save(doc, safe=True)
        return oid

    def update(self):
        self.data['atime'] = datetime.datetime.utcnow().strftime(TS_FORMAT)
        oid = self.collection.update({"_id" : self.data["_id"] },
                                     self.data,
                                     manipulate=True,
                                     safe=True)
        return oid
