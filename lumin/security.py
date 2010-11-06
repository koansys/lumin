from datetime import datetime
from hashlib import sha224

from webob.exc import HTTPFound

from pyramid.chameleon_zpt import get_template
from pyramid.security import authenticated_userid
from pyramid.security import remember
from pyramid.security import forget
from pyramid.url import route_url


class GroupFinder:
    def __init__(self, collection_name='users'):
        self.collection_name = collection_name

    def __call__(self, userid, request):
        try:
            user = request.root.db[self.collection_name].find(
                {'username' : userid}).next()
        except StopIteration:
            user = None
        if user:
            return user['groups']
groupfinder = GroupFinder()


class Login:
    def __init__(self, api, collection_name='users'):
        self.api = get_template(api)
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
                user = request.root.db[self.collection_name].find(
                    {'username' : login}).next()
            except StopIteration:
                user = None
            if user:
                if sha224(password).hexdigest() == user['password']:
                    headers = remember(request, login)
                    
                    request.root.db[self.collection_name].update(
                        {"_id" : user['_id']}, 
                        {"$set" : {'last_login' : datetime.now()}}
                         )
                    return HTTPFound(location=came_from,
                                     headers=headers)
            message = 'Login failed'

        return dict(
            api = self.api,
            came_from = came_from,
            logged_in = authenticated_userid(request),
            login = login,
            message = message,
            password = password,
            section = 'login',
            title = 'ravel | Log in',
            url = request.application_url + '/login',
            )
login = Login()


class Logout:
    def __init__(self, view_name='home'):
        self.view_name = view_name
    
    def __call__(self, request):
        headers = forget(request)
        return HTTPFound(location=route_url(self.view_name, request),
                         headers = headers)
logout = Logout()

