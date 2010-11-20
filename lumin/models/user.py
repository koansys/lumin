import datetime 
from webob.exc import HTTPInternalServerError

import colander
from colander import Float
from colander import SchemaNode
from colander import String

import deform

from pyramid.exceptions import NotFound
from pyramid.security import authenticated_userid
from pyramid.security import Allow
from pyramid.security import Everyone

from lumin import RootFactory
from lumin.util import reset
from lumin.util import TS_FORMAT

@colander.deferred
def deferred_username_validator(node, kw):
    request = kw['request']
    def validate_username(node, value):
        collection = request.context.collection
        available = collection.find({'_id': value}).count()==0
        if not available:
            raise colander.Invalid(node, "Username is not available")
    return validate_username

email_widget = deform.widget.CheckedInputWidget(
    subject="Email",
    confirm_subject="Confirm Email",
    size=40
    )

class EmailSchema(colander.Schema):
    email = SchemaNode(String(),
                       title="email",
                       description='Type your email address and confirm it',
                       validator=colander.Email(),
                       widget=email_widget)


class PasswordSchema(colander.Schema):
    password = SchemaNode(String(),
                          validator=colander.Length(min=6),
                          widget = deform.widget.CheckedPasswordWidget(size=40),
                          description="Type your password and confirm it")


class UserSchema(colander.MappingSchema):
    _id = SchemaNode(String(),
                     title="Username",
                     description="The name of the participant",
                     validator=deferred_username_validator)
    given_name = SchemaNode(String(), missing='',
                            title="Given Name")
    surname = SchemaNode(String(), missing='',
                         title="Surname")
    street_address = SchemaNode(String(), missing='',
                                title="Street Address",
                                description='Address info (number, street, unit)')
    locality = SchemaNode(String(), missing='',
                      title='City',
                      description="City or township name")
    ## TODO: There must be an ISO list for this
    region = SchemaNode(String(), missing='',
                       title='Locality',
                       description='State, Province, Township or equivalent')
    postal_code = SchemaNode(String(), missing='',
                             title='Postal Code',
                             description='ZIP or postal code')
    ## TODO: make this oneOf ISO countries
    country_name = SchemaNode(String(), missing='',
                              title='Country',
                              description='Country')
    telephone = SchemaNode(String(), missing='',
                       title='Telephone Number')
    fax = SchemaNode(String(), missing='',
                     title='Fax number')
    website_url = SchemaNode(String(), missing='',
                             title='Website URL',
                             description='I.e. http://example.com')
    latitude = SchemaNode(Float(), missing=colander.null,
                          title='Latitude')
    longitude = SchemaNode(Float(), missing=colander.null,
                           title='Longitude')
    email = SchemaNode(String(),
                       title="email",
                       description='Type your email address and confirm it',
                       validator=colander.Email(),
                       widget=email_widget)
    password = SchemaNode(String(),
                          validator=colander.Length(min=6),
                          widget = deform.widget.CheckedPasswordWidget(size=40),
                          description="Type your password and confirm it")

class SimpleUserSchema(colander.MappingSchema):
    _id = SchemaNode(String(),
                         title="Username",
                         description="The name of the participant",
                         validator=deferred_username_validator)
    display_name = SchemaNode(String(), missing=colander.null,
                              title="Display Name",
                              widget=deform.widget.TextInputWidget(size=40))
    email = SchemaNode(String(),
                       title="email",
                       description='Type your email address and confirm it',
                       validator=colander.Email(),
                       widget=email_widget)
    password = SchemaNode(String(),
                          validator=colander.Length(min=6),
                          widget = deform.widget.CheckedPasswordWidget(size=40),
                          description="Type your password and confirm it")



class User(RootFactory):

    __acl__ = [
        (Allow, Everyone, 'view'), ## Really?
        (Allow, Everyone, ('add')),
        (Allow, 'group:users', ('add', 'edit')),
        (Allow, 'group:managers', ('add', 'edit', 'delete')),
        ]

    __parent__ = __collection__ = 'users'
    __schema__ = UserSchema

    def __init__(self, request):
        super(User, self).__init__(request)
        self.request = request
        self.environ = request.environ
        self.collection = self.db[self.__collection__]
        self.schema = self.__schema__().bind(request=self.request)
        self.logged_in = authenticated_userid(request)
        self.user_id = request.matchdict.get('participant_id')
        if self.user_id == self.logged_in:
            if (Allow, self.user_id, ('edit', 'delete')) not in self.__acl__:
                self.__acl__.append((Allow, self.user_id, ('edit', 'delete')))
        if self.user_id != self.logged_in:
            if (Allow, self.logged_in, ('edit', 'delete')) in self.__acl__:
                self.__acl__.remove((Allow, self.logged_in, ('edit', 'delete')))
        if self.user_id:
            cursor = self.collection.find(
                {'_id' : self.user_id}
                )
            try:
                assert cursor.count() < 2
                self.data = cursor.next()
            except StopIteration:
                raise NotFound
            except AssertionError:
                raise HTTPInternalServerError

    def add_form(self):
        buttons = (deform.form.Button(name = "submit",
                                        title = "Create user"
                                        ),
                   reset)
        form = deform.Form(self.schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)

    def edit_form(self):
        buttons = (deform.form.Button(name = "submit",
                                        title = "Update user"
                                        ),
                   reset)
        form = deform.Form(self.schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)

    def insert(self, doc):
        ctime = atime = datetime.datetime.utctime().strftime(TS_FORMAT)
        doc['ctime'] = ctime
        doc['atime'] = atime
        oid = self.collection.save(doc, safe=True)
        return oid

    def update(self):
        self.data['atime'] = datetime.datetime.utctime().strftime(TS_FORMAT)
        oid = self.collection.update({"_id" : self.data["_id"] },
                                     self.data,
                                     manipulate=True,
                                     safe=True)
        return oid
