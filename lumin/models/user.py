from pyramid.security import authenticated_userid
from pyramid.security import Allow
from pyramid.security import Everyone

from lumin.node import ContextById
from lumin.schema import UserSchema


class User(ContextById):
    __acl__ = [
        (Allow, Everyone, 'view'),  # Really?
        (Allow, 'group:managers', 'edit'),
        ]

    collection = 'users'
    schema = UserSchema

    def __init__(self, request):
        super(User, self).__init__(request)
        self.logged_in = authenticated_userid(request)
        self._id = request.matchdict.get('slug')

        if self._id == self.logged_in:
            if (Allow, self._id, ('edit', 'delete')) not in self.__acl__:
                self.__acl__.append((Allow, self._id, ('edit', 'delete')))

        if self._id != self.logged_in:
            if (Allow, self.logged_in, ('edit', 'delete')) in self.__acl__:
                self.__acl__.remove((Allow, self.logged_in, ('edit', 'delete')))
