from flask import g
from foosweb.forms.player import LoginForm
from flask.ext.login import current_user

import pdb
import logging
log = logging.getLogger(__name__)

class BaseData():
    """base data, populates base.html template based on current user"""
    menu_items = (('Home', '/'), ('Players', '/players'), ('Teams', '/teams'), ('Tournaments', '/tournaments'), ('History', '/history'), ('Readme', '/readme'))

    def __init__(self):
        pass
        #self.auth = Auth()

    @classmethod
    def GetBaseData(self):
        data = {}
        data['menu'] = self.menu_items
        if current_user.is_authenticated():
            data['user_profile_url'] = '/players/%s' % (str(current_user.id))
            data['user_name'] = current_user.name
            data['user_id'] = current_user.id
            #if self.auth._is_admin(current_user.id):
            #data['admin'] = True
        else:
            data['anonymous'] = True
            data['id'] = -1
            data['loginform'] = LoginForm()
        #TODO: fix this and templates to be consistent (menu_item > current_view)
        data['current_view'] = g.get('menu_item', None)

        return data
