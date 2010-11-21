import re
import unicodedata

from pymongo.errors import DuplicateKeyError

from pyramid.chameleon_zpt import get_template
from pyramid.security import Allow
from pyramid.security import Everyone
from pyramid.settings import get_settings


def insert_doc(collection, document, title_or_id, key='_id', safe=True):
    """
    TODO: Insert a doc with a suffixed id if necessary as our unique id, and return
    TODO: prolly not ready for use yet. I just put a sanitized copy of this here.
    TODO: but it needs more though.
    """
    suffix=0
    collection.ensure_index(key, unique=True)
    url_id = normalize(title_or_id)
    document[key] = url_id
    while True:
        ## TODO: possible perfomance penalty
        ## If there are many of a given duplicate id
        ## this will me an expensive loop. otherwise no big
        ## deal. 
        ## TODO: add to api docs
        try:
            oid = collection.insert(document, safe=safe)
            return document[key]
        except DuplicateKeyError, e:
            suffix+=1
            url_id_suffixed = u','.join([url_id,
                                         unicode(suffix)])
            document[key] = url_id_suffixed

def normalize(title):
    """
    make url ready string/id from a title
    """
    url_safer = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore')
    url_safe = unicode(re.sub('[^\w\s-]', '', url_safer).strip().lower())
    return re.sub('[-\s]+', '-', url_safe)


class RootFactory(object):
    __acl__ = [ (Allow, Everyone, 'view'),]
    __name__ = __parent__ = None
    __collection__ = None
    def __init__(self, request, collection=None):
        settings = get_settings()
        self.db = request.db
        self.fs = request.fs
        if request.get('mc', None):
            self.mc = request.mc


class View:
    def __init__(self, api=None, collection_name='users'):
        if api:
            self.api = get_template(api)
        else:
            self.api = api
            self.collection_name = collection_name
