from datetime import datetime
from hashlib import sha256
import hmac

from webob.exc import HTTPFound

from pyramid.security import authenticated_userid
from pyramid.security import remember
from pyramid.security import forget
from pyramid.settings import get_settings
from pyramid.url import route_url
from pyramid.view import view_config


from lumin.util import TS_FORMAT

COLLECTION = 'users'

class GroupFinder:
    def __init__(self, collection_name=COLLECTION):
        self.collection_name = collection_name

    def __call__(self, userid, request):
        try:
            user = request.db[self.collection_name].find(
                {'_id' : userid}).next()
        except StopIteration:
            user = None
        if user and not user.get('disabled', None):
            return user['groups']
groupfinder = GroupFinder()


class Login:
    def __init__(self, collection_name=COLLECTION):
        self.collection_name = collection_name

    def __call__(self, request):
        login_url = route_url('login', request)
        referrer = request.url
        if referrer == login_url:
            referrer = '/'
        came_from = request.params.get('came_from', referrer)
        message = login = password = ''
        if 'form.submitted' in request.params:
            login = request.params['login']
            password = request.params['password']
            try:
                user = request.db[self.collection_name].find(
                    {'_id' : login}).next()
            except StopIteration:
                user = None
            if user and not user.get('disabled', None):
                settings = get_settings()
                challenged = hmac.new(settings['secret'], password, sha256).hexdigest()
                if challenged == user['password']:
                    headers = remember(request, login)

                    request.db[self.collection_name].update(
                        {"_id" : user['_id']},
                        {"$set" : {'last_login' : datetime.utcnow().strftime(TS_FORMAT)}}
                         )
                    return HTTPFound(location=came_from,
                                     headers=headers)
            message = 'Login failed'

        return dict(
            came_from = came_from,
            logged_in = authenticated_userid(request),
            login = login,
            message = message,
            password = password,
            title = 'Please log in',
            action = '/login',
            )


@view_config(context='pyramid.exceptions.Forbidden',
             renderer="lumin:templates/login.pt")
@view_config(route_name='login', renderer="lumin:templates/login.pt")
def login(context, request):
    return Login()(request)


class Logout:
    def __init__(self, view_name='home'):
        self.view_name = view_name

    def __call__(self, request):
        headers = forget(request)
        return HTTPFound(location=route_url(self.view_name, request),
                         headers = headers)


@view_config(route_name='logout')
def logout(context, request):
    request.session.flash('You have been logged out.')
    return Logout()(request)


def add_loginout(config):
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
