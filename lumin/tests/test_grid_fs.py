from __future__ import unicode_literals

import unittest

from mock import (
    Mock,
    MagicMock
    )
import mongomock

import pymongo

from pyramid.compat import (
    bytes_,
    text_
    )
import pyramid.testing

from lumin.testing import MockGridFS


class BaseTestCase(unittest.TestCase):
    request_path = '/'

    def setUp(self):

        self.request = pyramid.testing.DummyRequest(
            path=self.request_path,
            )

        self.config = pyramid.testing.setUp(
            request=self.request,
            settings={
                'secret': 'secret',
                'db_name': 'test',
                }
            )

        self.config.include('lumin')
        self.mock_conn = mongomock.Connection()
        self.mock_db = mongomock.Database(self.mock_conn)


class TestMongoUploadTmpStore(BaseTestCase):

    def make_one(self,
                 request=None,
                 image_mimetypes=('image/jpeg', 'image/png', 'image/gif'),
                 max_age=3600):
        from lumin.grid_fs import MongoUploadTmpStore
        if not request:
            request = self.request
        self.mock_fs = MockGridFS(
            self.mock_db,
            collection=MongoUploadTmpStore.__collection__)
        return MongoUploadTmpStore(
            request,
            gridfs=self.mock_fs,
            tempstore=self.mock_fs.collection,
            image_mimetypes=image_mimetypes,
            max_age=max_age)

    def _make_fp(self, data='fp'):
        from io import BytesIO
        return BytesIO(bytes_(data))

    def test_get_miss_explicit_default(self):
        inst = self.make_one()
        default = object()
        result = inst.get('uid', default)
        self.assertEqual(result, default)

    def test_get_miss_implicit_default(self):
        inst = self.make_one()
        result = inst.get('uid')
        self.assertEqual(result, None)

    def test_get_no_image(self):
        default = object()
        inst = self.make_one()
        result = inst.get('uid', default)
        self.assertEqual(result, default)

    def test_get_with_image(self):
        fp = self._make_fp()
        default = object()
        inst = self.make_one()
        inst.fs.put(fp, filename='abc', uid='theuid')
        result = inst.get('theuid', default)
        self.failUnless('abc' in inst.fs.list())
        self.assertEqual(result['fp'].read(), b'fp')

    def test___getitem__miss(self):
        inst = self.make_one()
        self.assertRaises(KeyError, inst.__getitem__, 'uid')

    def test___getitem__hit(self):
        fp = self._make_fp()
        inst = self.make_one()
        inst.fs.put(fp, filename='abc', uid='uid', mimetype='atype')
        self.assertEqual(inst['uid']['filename'], 'abc')
        self.assertEqual(inst['uid']['mimetype'], 'atype')
        self.assertEqual(inst['uid']['fp'].read(), self._make_fp().read())

    def test___contains__hit(self):
        fp = self._make_fp()
        inst = self.make_one()
        inst.fs.put(fp, filename='abc', uid='anuid')
        self.assertEqual(inst.__contains__('anuid'), True)

    def test___contains__miss(self):
        inst = self.make_one()
        self.assertEqual(inst.__contains__('uid'), False)

    def test___setitem__(self):
        fp = self._make_fp()
        cstruct = {'fp': fp,
                   'mimetype': 'mimetype',
                   'filename': 'filename',
                   'uid': 'uid'}
        inst = self.make_one()
        inst['uid'] = cstruct
        one = inst.tempstore.files.find_one({'uid': 'uid'})
        self.assertEqual(one['mimetype'], 'mimetype')
        self.assertEqual(one['uid'], 'uid')
        self.assertEqual(one['filename'], 'filename')
        self.assertEqual(one['length'], 2)
        self.failUnless(one['uploadDate'])
        self.failUnless(cstruct['filename'] in inst.fs.list())

    def test_preview_url(self):
        self.config.begin(request=self.request)
        self.config.add_route('preview_image', '/preview_image/:uid')
        fp = self._make_fp()
        inst = self.make_one()
        cstruct = {'fp': fp,
                   'mimetype': 'image/png',
                   'filename': 'filename',
                   'uid': 'uid'}
        inst['uid'] = cstruct
        self.assertEqual(inst.preview_url('uid'),
                         None)  # 'http://example.com/preview_image/uid')

    def test___delitem__(self):
        fp = self._make_fp()
        cstruct = {'fp': fp,
                   'mimetype': 'mimetype',
                   'filename': 'filename',
                   'uid': 'uid'}
        inst = self.make_one()
        inst['uid'] = cstruct
        self.failUnless(cstruct['filename'] in inst.fs.list())
        del inst[cstruct['uid']]
        self.failIf(cstruct['filename'] in inst.fs.list())

    def test_preview_url_not_image(self):
        self.config.begin(request=self.request)
        self.config.add_route('preview_image', '/preview_image/:uid')
        fp = self._make_fp()
        inst = self.make_one()
        cstruct = {'fp': fp,
                   'mimetype': 'text/html',
                   'filename': 'filename',
                   'uid': 'uid'}
        inst['uid'] = cstruct
        self.assertEqual(inst.preview_url('uid'), None)




class TestGridFile(BaseTestCase):

    metadata = {'uploaded_by': 'testuser',
                'mimetype': 'text/plain',
                '__acl__': ['Allow', 'system.Everyone', 'view']}

    def make_one(self, request=None):
        from lumin.grid_fs import GridFile
        if not request:
            request = self.request
        return GridFile(request)

    def _make_fs(self):
        mock_fs = MockGridFS(self.mock_db)
        self.request.fs = mock_fs
        return mock_fs

    def _make_file(self):
        from io import BytesIO
        return BytesIO(b'This is a file')

    def test_not_found(self):
        from pyramid.httpexceptions import HTTPNotFound
        self._make_fs()
        self.request.matchdict = {'slug': 'not gonna find it'}
        self.assertRaises(HTTPNotFound, self.make_one, request=self.request)

    def test_no_slug(self):
        from pyramid.httpexceptions import HTTPNotFound
        self._make_fs()
        self.assertRaises(HTTPNotFound, self.make_one, request=self.request)

    def test_found(self):
        fs = self._make_fs()
        fp = self._make_file()
        oid = fs.put(fp, content_type='text/plain',
                     filename='aname.txt',
                     metadata=self.metadata)
        self.request.matchdict = {'slug': str(oid)}
        result = self.make_one(request=self.request)
        self.assertEqual(result.gf.filename, 'aname.txt')
        self.assertEqual(result.gf.metadata, self.metadata)
        self.assertEqual(result.gf.read(), b'This is a file')

    def test__acl__explicit(self):
        fs = self._make_fs()
        fp = self._make_file()
        oid = fs.put(fp, content_type='text/plain',
                     filename='aname.txt',
                     metadata=self.metadata)
        self.request.matchdict = {'slug': str(oid)}
        result = self.make_one(request=self.request)
        self.assertEqual(result.__acl__,
            self.metadata['__acl__'])

    def test_response(self):
        from pyramid.response import Response
        fs = self._make_fs()
        fp = self._make_file()
        oid = fs.put(fp, content_type=text_('text/plain'),
                     filename='aname.txt',
                     xmetadata=self.metadata)
        self.request.matchdict = {'slug': str(oid)}
        result = self.make_one(request=self.request)
        resp = result.response()
        self.assertTrue(isinstance(resp, Response))
        self.assertEqual(resp.content_length, result.gf.length)
        self.assertEqual(resp.content_type, result.gf.content_type)
        self.assertEqual(resp.content_disposition,
                         'attachment; filename=aname.txt')
        self.assertEqual(resp.body, b'This is a file')
        self.assertEqual(resp.status, '200 OK')
