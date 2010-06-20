import re
import unicodedata

from pymongo.errors import DuplicateKeyError

def insert_doc(collection, document, key='url_id', safe=True):
    """
    TODO: Insert a doc with a suffixed id if necessary as our unique id, and return
    TODO: prolly not ready for use yet. I just put a sanitized copy of this here.
    TODO: but it needs more though.
    """
    suffix = 1
    url_id = document[key]
    while True:
        ## TODO: possible perfomance penalty
        ## If there are many of a given duplicate id
        ## this will me an expensive loop. otherwise no big
        ## deal. 
        ## TODO: add to api docs
        try:
            collection.ensure_index(key, unique=True)
            oid = collection.insert(document, safe=safe)
            return url_id
        except DuplicateKeyError, e:
            url_id_suffixed = u','.join([url_id,
                                         unicode(suffix)])
            document[key] = url_id_suffixed
            suffix+=1
            return url_id_suffixed

def normalize(title):
    """
    make url ready string/id from a title
    """
    url_safe = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore')
    url_safe = unicode(re.sub('[^\w\s-]', '', url_safe).strip().lower())
    return re.sub('[-\s]+', '-', url_safe)
