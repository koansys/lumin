import deform
import re
import unicodedata

from chameleon.utils import Markup as Structure


TS_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def normalize(title):
    """
    make an URL resource name ready for use in a URL. Essentially it
    takes a string representing an id or title and makes it character
    safe for use in a URL. In ``lumin`` this is likely to be the
    :term:`_id` or the :term:`__name__` by which we find the resource.
    """
    url_safer = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore')
    url_safe = unicode(re.sub('[^\w\s-]', '', url_safer).strip().lower())
    return re.sub('[-\s]+', '-', url_safe)



## buttons
reset = deform.form.Button(name='reset', title='Reset',
                           type='reset', value='reset')

##TODO: need to fork deform and make button take onClick
cancel = deform.form.Button(name='cancel', title='Cancel',
                            type='button', value='cancel',)
"""
To use this cancel button you must include some javascript
$(document).ready(function () {
    $(function () {
           $("#deformcancel").attr('onClick', "history.back()");
       });
});
"""

