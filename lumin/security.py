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
            return user['groups']

groupfinder = GroupFinder()
