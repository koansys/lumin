import colander


@colander.deferred
def deferred_username_validator(node, kw):
    request = kw['request']

    def validate_username(node, value):
        if len(value) < 4 or len(value) > 24:
            raise colander.Invalid(node,
                                   "Length of user name must be between 4 and \
                                    24 lowercase alphanumeric characters")
        if not value.replace('_', '').isalnum() or not value.islower():
            raise colander.Invalid(node,
                                "Only lowercase numbers, letters and \
                                underscores are permitted")
        if not value[0].isalpha():
            raise colander.Invalid(node,
                                   "The username must start with a \
                                   letter")

        query = request.context.find(_id=value)

        if query.count() > 0:
            raise colander.Invalid(node, "Username is not available")

    return validate_username


