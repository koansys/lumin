from pyramid.security import (
    Allow,
    Everyone
    )


class Factory(object):
    """Pyramid `resource nee context <http://bit.ly/pyramid-latest-resources>`
    factory base class.
    """

    _default__acl__ = __acl__ = [
              [Allow, Everyone, 'view'],
              ]

    __name__ = __parent__ = None

    def __init__(self, request):
        self.data = {}
        self.request = request
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
            lambda ace: \
            ace[2] if isinstance(ace[2], list) else True,
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
