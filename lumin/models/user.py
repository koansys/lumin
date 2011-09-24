from pyramid.security import authenticated_userid
from pyramid.security import Allow
from pyramid.security import Everyone
from pyramid.security import has_permission

from lumin.node import ContextById
from lumin.node import Collection


class UserManagement(Collection):
    __acl__ = (
        [Allow, Everyone, 'join'],
        [Allow, 'group:managers', ['add', 'manage', 'delete']],
        )

    collection = 'users'

    def get(self, _id):
        return User(self.request, _id=_id)


class User(ContextById):
    _default__acl__ = [
        [Allow, 'group:managers', ['view', 'edit', 'delete', 'manage', 'add']],
        ]

    collection = 'users'

    def __init__(self, request, **kwargs):
        super(User, self).__init__(request, **kwargs)

        if self._id == authenticated_userid(request):
            permissions = tuple(
                permission for permission in ('view', 'edit') if
                not has_permission(permission, self, request)
                )

            if permissions:
                self.add_ace([Allow, self._id, list(permissions)])
