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

# from lumin.testing.base import BaseFunctionalTestCase


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
        self.request.db = self.mock_db
        self.mock_tempstore = mongomock.Collection(self.mock_db)
        self.mock_files = mongomock.Collection(self.mock_db)
        self.request.db.tempstore = self.mock_tempstore
        self.request.db.tempstore.files = self.mock_files


class TestMongoUploadTmpStore(BaseTestCase):

    def make_one(self,
                 request=None,
                 gridfs=None,
                 image_mimetypes=('image/jpeg', 'image/png', 'image/gif'),
                 max_age=3600):
        from lumin.grid_fs import MongoUploadTmpStore
        if not request:
            request = self.request
        return MongoUploadTmpStore(request,
                                   gridfs=gridfs,
                                   tempstore=self.request.db.tempstore,
                                   image_mimetypes=image_mimetypes,
                                   max_age=max_age)

    def _make_fs(self):
        from gridfs import GridFS
        fs = Mock(spec=GridFS)
        return fs

    def _make_fp(self, data='fp'):
        from io import BytesIO
        return BytesIO(bytes_(data))

    def test_get_miss_explicit_default(self):
        inst = self.make_one(
            gridfs=self._make_fs(),
            )
        default = object()
        result = inst.get('uid', default)
        self.assertEqual(result, default)

    def test_get_miss_implicit_default(self):
        inst = self.make_one(
            gridfs=self._make_fs())
        result = inst.get('uid')
        self.assertEqual(result, None)

    def test_get_no_image(self):
        default = object()
        inst = self.make_one(
            gridfs=self._make_fs())
        result = inst.get('uid', default)
        self.assertEqual(result, default)

    def test_get_with_image(self):
        fs = self._make_fs()
        # fs.list = MagicMock(return_value=['abc'])
        fp = self._make_fp()
        fs.put(fp, filename='abc', uid='theuid')
        default = object()
        inst = self.make_one(gridfs=fs)
        result = inst.get('theuid', default)
        self.failUnless('abc' in inst.fs.list())
        self.assertEqual(result['fp'].read(), b'fp')

#     def test___getitem__miss(self):
#         inst = self.make_one()
#         self.assertRaises(KeyError, inst.__getitem__, 'uid')

#     def test___getitem__hit(self):
#         fs = self._make_fs()
#         fp = self._make_fp()
#         fs.put(fp, filename='abc', uid='uid', mimetype='atype')
#         inst = self.make_one(gridfs=fs)
#         self.assertEqual(inst['uid']['filename'], 'abc')
#         self.assertEqual(inst['uid']['mimetype'], 'atype')
#         self.assertEqual(inst['uid']['fp'].read(), self._make_fp().read())

#     def test___contains__hit(self):
#         fs = self._make_fs()
#         fp = self._make_fp()
#         fs.put(fp, filename='abc', uid='anuid')
#         inst = self.make_one(gridfs=fs)
#         self.assertEqual(inst.__contains__('anuid'), True)

#     def test___contains__miss(self):
#         inst = self.make_one()
#         self.assertEqual(inst.__contains__('uid'), False)

#     def test___setitem__(self):
#         fp = self._make_fp()
#         cstruct = {'fp': fp,
#                    'mimetype': 'mimetype',
#                    'filename': 'filename',
#                    'uid': 'uid'}
#         inst = self.make_one()
#         inst['uid'] = cstruct
#         one = self.request.db.tempstore.files.find_one({'uid': 'uid'})
#         self.assertEqual(one['mimetype'], 'mimetype')
#         self.assertEqual(one['uid'], 'uid')
#         self.assertEqual(one['filename'], 'filename')
#         self.assertEqual(one['length'], 2)
#         self.failUnless(one['uploadDate'])
#         self.failUnless(cstruct['filename'] in inst.fs.list())

#     def test_preview_url(self):
#         self.config.begin(request=self.request)
#         self.config.add_route('preview_image', '/preview_image/:uid')
#         fp = self._make_fp()
#         fs = self._make_fs()
#         inst = self.make_one(gridfs=fs)
#         cstruct = {'fp': fp,
#                    'mimetype': 'image/png',
#                    'filename': 'filename',
#                    'uid': 'uid'}
#         inst['uid'] = cstruct
#         self.assertEqual(inst.preview_url('uid'),
#                          None)  # 'http://example.com/preview_image/uid')

#     def test_preview_url_not_image(self):
#         self.config.begin(request=self.request)
#         self.config.add_route('preview_image', '/preview_image/:uid')
#         fp = self._make_fp()
#         fs = self._make_fs()
#         inst = self.make_one(gridfs=fs)
#         cstruct = {'fp': fp,
#                    'mimetype': 'text/html',
#                    'filename': 'filename',
#                    'uid': 'uid'}
#         inst['uid'] = cstruct
#         self.assertEqual(inst.preview_url('uid'), None)


# class TestGridFile(BaseTestCase):

#     metadata = {'uploaded_by': 'testuser',
#                 'mimetype': 'text/plain',
#                 '__acl__': ['Allow', 'system.Everyone', 'view']}

#     def make_one(self, request=None):
#         from lumin.grid_fs import GridFile
#         if not request:
#             request = self.request
#         return GridFile(request)

#     def _make_fs(self):
#         from gridfs import GridFS
#         fs = GridFS(self.request.db)
#         return fs

#     def _make_file(self):
#         from io import BytesIO
#         return BytesIO(b'This is a file')

#     def test_not_found(self):
#         from pyramid.httpexceptions import HTTPNotFound
#         self.request.matchdict = {'slug': 'not gonna find it'}
#         self.assertRaises(HTTPNotFound, self.make_one, request=self.request)

#     def test_no_slug(self):
#         from pyramid.httpexceptions import HTTPNotFound
#         self.assertRaises(HTTPNotFound, self.make_one, request=self.request)

#     def test_found(self):
#         fs = self._make_fs()
#         fp = self._make_file()
#         oid = fs.put(fp, content_type='text/plain',
#                      filename='aname.txt',
#                      metadata=self.metadata)
#         self.request.matchdict = {'slug': str(oid)}
#         result = self.make_one(request=self.request)
#         self.assertEqual(result.gf.filename, 'aname.txt')
#         self.assertEqual(result.gf.metadata, self.metadata)
#         self.assertEqual(result.gf.read(), b'This is a file')

#     def test_response(self):
#         from pyramid.response import Response
#         fs = self._make_fs()
#         fp = self._make_file()
#         oid = fs.put(fp, content_type=text_('text/plain'),
#                      filename='aname.txt',
#                      xmetadata=self.metadata)
#         self.request.matchdict = {'slug': str(oid)}
#         result = self.make_one(request=self.request)
#         resp = result.response()
#         self.assertTrue(isinstance(resp, Response))
#         self.assertEqual(resp.content_length, result.gf.length)
#         self.assertEqual(resp.content_type, result.gf.content_type)
#         self.assertEqual(resp.content_disposition,
#                          'attachment; filename=aname.txt')
#         self.assertEqual(resp.body, b'This is a file')
#         self.assertEqual(resp.status, '200 OK')
