from __future__ import unicode_literals


COLLECTION = 'users'


class GroupFinder:
    def __init__(self, collection_name=COLLECTION):
        self.collection_name = collection_name

    def __call__(self, userid, request):
        try:
            user = next(request.db[self.collection_name].find(
                {'_id': userid}))
        except StopIteration:
            user = None
        if user and not user.get('disabled', None):
            groups = set(user['groups'])

            try:
                roles = request.context.data['__roles__']
            except (AttributeError, KeyError):
                return groups

            if roles:  # pragma: no branch
                principals = set(groups)
                principals.add(user['_id'])
                check = principals.__contains__

                for role, principals in roles.items():
                    if any(check(p) for p in principals):
                        groups.add(role)

            return groups

groupfinder = GroupFinder()


class BootstrapAuthenticationPolicy(object):
    def __init__(self, policy, *principals):
        self.policy = policy
        self.principals = list(principals)

    def __getattr__(self, name):
        return getattr(self.policy, name)

    def effective_principals(self, request):
        principals = self.policy.effective_principals(request)
        return list(principals) + self.principals
