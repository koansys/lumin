from webob.exc import HTTPNotFound
from webob.exc import HTTPInternalServerError

import colander
from colander import Float
from colander import SchemaNode
from colander import String

import deform

from pyramid.security import authenticated_userid
from pyramid.security import Allow
from pyramid.security import Everyone

from lumin import RootFactory
from lumin.util import reset


email_widget = deform.widget.CheckedInputWidget(
    subject="Email",
    confirm_subject="Confirm Email",
    size=40
    )

class EmailSchema(colander.MappingSchema):
    email = SchemaNode(String(),
                       title="email",
                       description='Type your email address and confirm it',
                       validator=colander.Email(),
                       widget=email_widget)


class PasswordSchema(colander.MappingSchema):
    password = SchemaNode(String(),
                          validator=colander.Length(min=6),
                          widget = deform.widget.CheckedPasswordWidget(size=40),
                          description="Type your password and confirm it")


class UserSchema(colander.MappingSchema):
    username = SchemaNode(String(),
                          title="User",
                          description="The name of the participant")
    given_name = SchemaNode(String(), missing='',
                            title="Given Name")
    surname = SchemaNode(String(), missing='',
                         title="Surname")
    email = EmailSchema()
    password = PasswordSchema()
    # email = SchemaNode(String(),
    #                    title="email",
    #                    description='Type your email address and confirm it',
    #                    validator=colander.Email(),
    #                    widget=email_widget)
    # password = SchemaNode(String(),
    #                       validator=colander.Length(min=6),
    #                       widget = deform.widget.CheckedPasswordWidget(size=40),
    #                       description="Type your password and confirm it")


class User(RootFactory):

    __acl__ = [
        (Allow, Everyone, 'view'), ## Really?
        (Allow, Everyone, ('add')),
        (Allow, 'group:users', ('add', 'edit')),
        (Allow, 'group:managers', ('add', 'edit', 'delete')),
        ]

    __parent__ = __collection__ = 'users'

    def __init__(self, request):
        super(User, self).__init__(request)
        self.request = request
        self.environ = request.environ
        self.collection = self.db[self.__collection__]
        self.logged_in = authenticated_userid(request)
        self.user_id = request.matchdict.get('url_id')
        if self.user_id:
            cursor = self.collection.find(
                {'__uid__' : self.user_id}
                )
            try:
                assert cursor.count() < 2
                self.user = cursor.next()
            except StopIteration:
                raise HTTPNotFound
            except AssertionError:
                raise HTTPInternalServerError

        self.schema = UserSchema()

    def add_form(self):
        buttons = (deform.form.Button(name = "submit",
                                        title = "Create user"
                                        ),
                   reset)
        form = deform.Form(self.schema, buttons=buttons)
        resources = form.get_widget_resources()
        return (form, resources)

    def insert(self, doc):
        pass
