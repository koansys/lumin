COLLECTION = 'users'


class GroupFinder:
    def __init__(self, collection_name=COLLECTION):
        self.collection_name = collection_name

    def __call__(self, userid, request):
        try:
            user = request.db[self.collection_name].find(
                {'_id': userid}).next()
        except StopIteration:
            user = None
        if user and not user.get('disabled', None):
            groups = set(user['groups'])

            try:
                roles = request.context.data['__roles__']
            except (AttributeError, KeyError):
                return groups

            if roles:
                principals = set(groups)
                principals.add(user['_id'])
                check = principals.__contains__

                for role, principals in roles.items():
                    if any(check(p) for p in principals):
                        groups.add(role)

            return groups

groupfinder = GroupFinder()
