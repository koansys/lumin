import colander
from colander import Float
from colander import SchemaNode
from colander import String

from pyramid.security import authenticated_userid
from pyramid.security import Allow
from pyramid.security import Everyone

from lumin import RootFactory


class UserSchema(colander.MappingSchema):
    username = SchemaNode(String(),
                          title="User",
                          description="The name of the participant")
    given_name = SchemaNode(String(), missing='',
                            title="Given Name")
    surname = SchemaNode(String(), missing='',
                         title="Surname")
    street_address = SchemaNode(String(), missing='',
                                title="Street Address",
                                description='Address info (number, street, unit)')
    locality = SchemaNode(String(), missing='',
                      title='City',
                      description="City or township name")
    ## TODO: There must be an ISO list for this
    region = SchemaNode(String(), missing='',
                       title='Locality',
                       description='State, Province, Township or equivalent')
    postal_code = SchemaNode(String(), missing='',
                             title='Postal Code',
                             description='ZIP or postal code')
    ## TODO: make this oneOf ISO countries
    country_name = SchemaNode(String(), missing='',
                              title='Country',
                              description='Country')
    telephone = SchemaNode(String(), missing='',
                       title='Telephone Number')
    fax = SchemaNode(String(), missing='',
                     title='Fax number')
    website_url = SchemaNode(String(), missing='',
                             title='Website URL',
                             description='I.e. http://example.com')
    latitude = SchemaNode(Float(), missing=colander.null,
                          title='Latitude')
    longitude = SchemaNode(Float(), missing=colander.null,
                           title='Longitude')


                         
class User(RootFactory):

    __acl__ = [
        (Allow, Everyone, 'view'), ## Really?
        (Allow, Everyone, ('add')),
        (Allow, 'group:users', ('add', 'edit')),
        (Allow, 'group:managers', ('add', 'edit', 'delete')),
        ]

    __parent__ = __collection__ = 'users'
    
    def __init__(self, request):
        super(User, self).__init__(request)
        self.request = request
        self.environ = request.environ
        self.collection = self.db[self.__collection__]
        self.logged_in = authenticated_userid(request)
        self.user_id = request.matchdict.get('url_id')
        if self.user_id:
            cursor = self.collection.find(
                {'url_id' : self.participant_id}
                )
            try:
                self.user = cursor.next()
            except StopIteration:
                self.user = None
            
            assert cursor.count() == 1
        self.schema = UserSchema()
        
        
