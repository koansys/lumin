import re

from webob.exc import HTTPNotFound


def autocomplete_id(request):
    collection = request.matchdict.get('collection')
    if collection in request.db.collection_names():
        term = request.params.get('term')
        cursor = request.db[collection].find(
            {'_id' : re.compile('.*%s.*' % term, re.IGNORECASE)})
        return [term['_id'] for term in cursor]
    else:
        return HTTPNotFound

def autocomplete_name(request):
    """
    Auto completes by name
    """
    collection = request.matchdict.get('collection')
    if collection in request.db.collection_names():
        term = request.params.get('term')
        cursor = request.db[collection].find(
            {'name' : re.compile('.*%s.*' % term, re.IGNORECASE)})
        return [term['name'] for term in cursor]
    else:
        return HTTPNotFound

def word_suggest(request):
    text = request.params.get('term', None)
    cursor = request.db['words'].find(
        {'_id' : re.compile('^%s.*' % text, re.IGNORECASE) })
    return [text['_id'] for text in cursor]

  # Sample zcml config
  # <!-- Autocomplete views -->
  #   <route
  #     name="word_suggest"
  #     path="/suggest/words"
  #     permission="edit"
  #     renderer="json"
  #     view=".views.autocomplete.word_suggest"
  #     xhr="True"
  #     />
  #   <route
  #     name="autocomplete_id"
  #     path="/suggest/:collection"
  #     permission="edit"
  #     renderer="json"
  #     view=".views.autocomplete.autocomplete_id"
  #     xhr="True"
  #     />
  #   <route
  #     name="autocomplete_name"
  #     path="/name/:collection"
  #     permission="edit"
  #     renderer="json"
  #     view=".views.autocomplete.autocomplete_name"
  #     xhr="True"
  #     />
  # <!-- END: Autocomplete views -->
