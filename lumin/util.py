import deform


TS_FORMAT="%Y-%m-%d %H:%M:%S.%f"

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

