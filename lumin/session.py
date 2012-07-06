from __future__ import unicode_literals

import os  # pragma: no cover
import time   # pragma: no cover

from bson.objectid import ObjectId   # pragma: no cover

from zope.interface import implements  # pragma: no cover

from pyramid.interfaces import ISession  # pragma: no cover
from pyramid.session import manage_accessed  # pragma: no cover
from pyramid.session import signed_deserialize  # pragma: no cover
from pyramid.session import signed_serialize  # pragma: no cover


def LuminSessionFactoryConfig(
    secret,
    timeout=1200,
    cookie_name='lumin_session',
    cookie_max_age=None,
    cookie_path='/',
    cookie_domain=None,
    cookie_secure=False,
    cookie_httponly=False,
    cookie_on_exception=True,
    ):
    """
    Parameters:

    ``secret``
      A string which is used to sign the cookie.

    ``timeout``
      A number of seconds of inactivity before a session times out.

    ``cookie_name``
      The name of the cookie used for sessioning.  Default: ``session``.

    ``cookie_max_age``
      The maximum age of the cookie used for sessioning (in seconds).
      Default: ``None`` (browser scope).

    ``cookie_path``
      The path used for the session cookie.  Default: ``/``.

    ``cookie_domain``
      The domain used for the session cookie.  Default: ``None`` (no domain).

    ``cookie_secure``
      The 'secure' flag of the session cookie.  Default: ``False``.

    ``cookie_httponly``
      The 'httpOnly' flag of the session cookie.  Default: ``False``.

    ``cookie_on_exception``
      If ``True``, set a session cookie even if an exception occurs
      while rendering a view.  Default: ``True``.

    You can set the session collection name by adding a
    ``lumin.session.collection`` key/value to the configuration .ini
    """

    class LuminSessionFactory(dict):

        implements(ISession)

        # configuration parameters
        _cookie_name = cookie_name
        _cookie_max_age = cookie_max_age
        _cookie_path = cookie_path
        _cookie_domain = cookie_domain
        _cookie_secure = cookie_secure
        _cookie_httponly = cookie_httponly
        _cookie_on_exception = cookie_on_exception
        _secret = secret
        _timeout = timeout

        # dirty flag
        _dirty = False

        def __init__(self, request):
            self.request = request
            self.collection = request.registry.settings.get(
                "lumin.session.collection",
                "lumin.sessions")
            self.db = self.request.db

            now = time.time()
            created = accessed = now
            new = True
            value = None
            state = self._new_session()
            cookieval = request.cookies.get(self._cookie_name)

            if cookieval is not None:
                try:
                    value = signed_deserialize(cookieval, self._secret)

                except ValueError:
                    value = None

            if value is not None:
                accessed, created, oid = value
                new = False
                state = self.db[self.collection].find_one({'_id': oid})
                if not state:  # pragma: no cover
                    state = self._new_session()
                if now - accessed > self._timeout:
                    if state:
                        self.invalidate({'_id': state['_id']})
                    state = self._new_session()

            self.created = created
            self.accessed = accessed
            self.new = new
            dict.__init__(self, state)

        def _new_session(self):
            return {'_id': ObjectId()}

        # ISession methods
        def changed(self):
            return self._dirty

        def invalidate(self, spec=None):
            if not spec:
                spec = {'_id': self['_id']}
            self.db[self.collection].remove(spec)
            self.clear()
            # XXX probably needs to unset cookie

        def save(self):
            self.db[self.collection].save(self)

        # non-modifying dictionary methods
        get = manage_accessed(dict.get)
        __getitem__ = manage_accessed(dict.__getitem__)
        items = manage_accessed(dict.items)
        iteritems = manage_accessed(dict.iteritems)
        values = manage_accessed(dict.values)
        itervalues = manage_accessed(dict.itervalues)
        keys = manage_accessed(dict.keys)
        iterkeys = manage_accessed(dict.iterkeys)
        __contains__ = manage_accessed(dict.__contains__)
        has_key = manage_accessed(dict.has_key)
        __len__ = manage_accessed(dict.__len__)
        __iter__ = manage_accessed(dict.__iter__)

        # modifying dictionary methods
        clear = manage_accessed(dict.clear)
        update = manage_accessed(dict.update)
        setdefault = manage_accessed(dict.setdefault)
        pop = manage_accessed(dict.pop)
        popitem = manage_accessed(dict.popitem)
        __setitem__ = manage_accessed(dict.__setitem__)
        __delitem__ = manage_accessed(dict.__delitem__)

        # flash API methods
        @manage_accessed
        def flash(self, msg, queue='', allow_duplicate=True):
            storage = self.setdefault('_f_' + queue, [])
            if allow_duplicate or (msg not in storage):
                storage.append(msg)

        @manage_accessed
        def pop_flash(self, queue=''):
            storage = self.pop('_f_' + queue, [])
            return storage

        @manage_accessed
        def peek_flash(self, queue=''):
            storage = self.get('_f_' + queue, [])
            return storage

        # CSRF API methods
        @manage_accessed
        def new_csrf_token(self):
            token = os.urandom(20).encode('hex')
            self['_csrft_'] = token
            return token

        @manage_accessed
        def get_csrf_token(self):
            token = self.get('_csrft_', None)
            if token is None:
                token = self.new_csrf_token()
            return token

        # non-API methods
        def _set_cookie(self, response):
            if not self._cookie_on_exception:
                exception = getattr(self.request, 'exception', None)
                if exception is not None:  # don't set cookie during exceptions
                    return False

            self.save()
            cookieval = signed_serialize(
                (self.accessed, self.created, self['_id']), self._secret
                )
            response.set_cookie(
                self._cookie_name,
                value=cookieval,
                max_age=self._cookie_max_age,
                path=self._cookie_path,
                domain=self._cookie_domain,
                secure=self._cookie_secure,
                httponly=self._cookie_httponly,
                )
            return True

    return LuminSessionFactory
