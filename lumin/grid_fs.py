from datetime import datetime
from datetime import timedelta

from bson.objectid import ObjectId

from gridfs import GridFS
from gridfs.errors import NoFile
from bson.errors import InvalidId

from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.security import Allow
from pyramid.url import route_url


class MongoUploadTmpStore(object):
    __collection__ = 'tempstore'

    def __init__(self,
                 request,
                 gridfs=None,
                 image_mimetypes=('image/jpeg', 'image/png', 'image/gif'),
                 max_age=3600):
        self.request = request
        self.fs = gridfs if gridfs else GridFS(request.db,
                                               collection=self.__collection__)
        self.tempstore = request.db[self.__collection__]
        self.max_age = timedelta(seconds=max_age)
        self.image_mimetypes = image_mimetypes
        ## XXX: Total hackery
        ## TODO: remove when mongo gets TTL capped collections.
        expired = self.tempstore.files.find(
            {'uploadDate': {"$lt": datetime.utcnow() - self.max_age}})
        for file_ in expired:
            self.fs.delete(file_['_id'])

    def get(self, uid, default=None):
        result = self.tempstore.files.find_one({'uid': uid})
        if result is None:
            return default
        oid = result['_id']
        fp = self.fs.get(oid)
        if fp is None:
            return default
        result['fp'] = fp
        return result

    def __getitem__(self, uid):
        result = self.get(uid)
        if result is None:
            raise KeyError(uid)
        return result

    def __contains__(self, uid):
        return self.get(uid) is not None

    def __setitem__(self, oid, cstruct):
        fp = cstruct.get('fp')
        self.fs.put(
            fp,
            mimetype=cstruct.get('mimetype'),
            filename=cstruct.get('filename'),
            uid=cstruct.get('uid')
            )
        fp.seek(0)  # reset so view can read

    def __delitem__(self, uid):
        result = self.tempstore.files.find_one({'uid': uid})
        oid = result['_id']
        self.fs.delete(oid)

    def preview_url(self, uid):
        gf = self.get(uid)
        if gf and gf.get('mimetype') in self.image_mimetypes:
            return None #return route_url('preview_image', self.request, uid=uid)
        else:
            return None  # route_url('preview_image', self.request, uid=uid)


class GridFile:
    """
    GirdFile Factory
    """
    _default__acl__ = [
        (Allow, 'group:managers', ('add', 'delete', 'edit', 'view')),
        ]

    def __init__(self, request, **kwargs):
        self.fs = request.fs
        self._id = request.matchdict.get('slug', None)
        if not self._id:
            raise HTTPNotFound
        try:
            self.gf = self.fs.get(ObjectId(self._id))
        except (NoFile, InvalidId):
            raise HTTPNotFound(self._id)

    @property
    def __acl__(self):
        return self.gf.metadata.get('__acl__', self._default__acl__)

    def response(self):
        return Response(
            body=self.gf.read(),
            content_disposition='attachment; filename={}'.format(
                self.gf.filename.encode('utf8')),
            content_type=self.gf.content_type.encode('utf8') if \
                self.gf.content_type else 'binary/octet-stream',
            content_length=self.gf.length
            )



#@view_config(route_name='files')
# def grid_files(request):
#     return request.context.response()


#def add_gridfs_routes(config):
#    config.add_route('files',  '/files/{slug}')

