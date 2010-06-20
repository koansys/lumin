import re
import unicodedata

import pymongo
from pymongo.errors import DuplicateKeyError
from gridfs import GridFS 

#import memcache

from repoze.bfg.security import Allow
from repoze.bfg.security import Everyone

from repoze.bfg.settings import get_settings

from lumin.son import ColanderNullTransformer


def insert_doc(collection, document, title_or_id, key='url_id', safe=True):
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
    def __init__(self, request, collection=None):
        settings = get_settings()
        self.db = pymongo.Connection.from_uri(
            uri=settings['db_uri'])[settings['db_name']]
        self.db.add_son_manipulator(ColanderNullTransformer())
        self.fs = GridFS(self.db)
        #self.mc = memcache.Client(settings['mc_host'])


