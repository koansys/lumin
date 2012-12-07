from __future__ import unicode_literals
import unittest

import mongomock

import pyramid.testing


class TestGroupFinder(unittest.TestCase):
    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.request = pyramid.testing.DummyRequest()

        self.mock_conn = mongomock.Connection()
        self.request.db = mongomock.Database(self.mock_conn)
        self.request.db.users = mongomock.Collection(self.request.db)

    def tearDown(self):
        pyramid.testing.tearDown()

    def _call_fut(self, userid='auser', request=None):
        from lumin.security import GroupFinder
        gf = GroupFinder()
        return gf(userid, request)

    def _make_context(self):

        class Dummy:
            data = {"__roles__": {
                "arole": ["otheruser"],
                "brole": ["auser"]
            }}

        return Dummy()

    def test_user_doesnt_exist(self):
        result = self._call_fut(request=self.request)
        self.assertEquals(result, None)

    def test_user_exist_nogroups(self):
        self.request.db.users.insert({'_id': 'auser'})
        result = self._call_fut(request=self.request)
        self.assertEquals(result, None)

    def test_user_exists_agroup(self):
        self.request.db['users'].insert({
            '_id': 'auser',
            'groups': ['agroup']
            })
        result = self._call_fut(request=self.request)
        self.assertEqual(result, set(['agroup']))

    def test_user_exists_dupe_groups(self):
        self.request.db['users'].insert({
            '_id': 'auser',
            'groups': ['agroup', 'agroup']
            })
        result = self._call_fut(request=self.request)
        self.assertEqual(result, set(['agroup']))

    def test_user_exists_with_role(self):
        self.request.db['users'].insert({
            '_id': 'auser',
            'groups': ['agroup']
            })
        self.request.context = self._make_context()
        result = self._call_fut(request=self.request)
        self.assertEqual(result, set(['agroup', 'brole']))


class TestBootstrapAuthenticationPolicy(unittest.TestCase):
    def _make_one(self, *principals, **kwargs):
        from pyramid.authentication import AuthTktAuthenticationPolicy
        from lumin.security import BootstrapAuthenticationPolicy
        authpolicy = AuthTktAuthenticationPolicy('asecret', **kwargs)
        return BootstrapAuthenticationPolicy(authpolicy, *principals)

    def test_it(self):
        request = pyramid.testing.DummyRequest()
        inst = self._make_one("one", "two")
        self.assertEquals(inst.effective_principals(request),
            ["system.Everyone", "one", "two"])

    def test_attr(self):
        def dummy():
            pass
        inst = self._make_one("one", "two", callback=dummy)
        self.assertEquals(inst.callback, dummy)
