from flask.ext.wtf import Form
from wtforms import TextField
from wtforms.validators import DataRequired, ValidationError, Length

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import logging
import collections
from gettext import gettext

from hashlib import md5

from foosweb import PlayerData
from models import Player, Admin

import pdb

log = logging.getLogger('gamewatch')

class Auth():
    def __init__(self):
        db = create_engine('sqlite:///foosball.db')
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()

    #def Login(self, email, password):
    def Login(self, **kwargs):
        password = md5(kwargs['password']).hexdigest()
        email = str(kwargs['email']).strip().lower()
        try:
            player = self.session.query(Player).filter_by(email=email).filter_by(password=password).one()
        except NoResultFound:
            return

        player.authenticated = True
        self.session.add(player)
        self.session.commit()
        return True

    def Logout(self, current_player):
        player = self.GetPlayerByEmail(current_player.email)
        player.authenticated = False
        self.session.add(player)
        self.session.commit()

    def GetPlayerByEmail(self, email):
        email = str(email).strip().lower()
        try:
            player = self.session.query(Player).filter_by(email=email).one()
        except NoResultFound:
            return
        return player

    def GetPlayerByID(self, id):
        try:
            id = int(id)
        except ValueError, e:
            return

        try:
            player = self.session.query(Player).filter_by(id=id).one()
        except NoResultFound:
            return
        except Exception, e:
            log.error('Exception thrown trying to get player %s!' % (str(id)))
            return

        return player

    def IsAdmin(self, id):
        try:
            id = int(id)
        except ValueError, e:
            return

        try:
            admin = self.session.query(Admin).filter_by(player_id=id).one()
        except NoResultFound:
            return
        except Exception, e:
            log.error('Exception %s thrown checking admin status of  %s!' % (repr(e), str(id)))
            return

        return True

    def RequiresAdmin(self, func):
        pdb.set_trace()
        def wrapped_route(*args, **kwargs):
            pass

class LoginForm(Form):
    #TODO: figure out how the hell to get these error messages to display!
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address."))])
    password = TextField('password', validators = [DataRequired(message=gettext("Enter your password."))])
    auth = Auth()

class Menu():
    menu_items = [{'name': 'Home', 'url': '/'}, \
            {'name': 'History', 'url': '/history'}, \
            {'name': 'Readme', 'url': '/readme'}]

    def Make(self, user, entry):
        auth = Auth()
        menu = {}
        if user.is_authenticated():
            menu['name'] = user.name
            menu['id'] = user.id
            if auth.IsAdmin(user.id):
                menu['menu'] = dict(({'name': 'Admin', 'url': '/admin'}).items() + (item for item in self.menu_items if item['name'] != entry))
        else:
            menu['anonymous'] = True

        menu['menu'] = (item for item in self.menu_items if item['name'] != entry)
        return collections.OrderedDict(sorted(menu.items()))


class RenderData():
    menu_items = (('Home', '/'), ('History', '/history'), ('Readme', '/readme'))

    def __init__(self):
        self.auth = Auth()

    def Get(self, user):
        data = {}
        data['menu'] = self.menu_items
        if user.is_authenticated():
            data['name'] = user.name
            data['id'] = user.id
            if self.auth.IsAdmin(user.id):
                data['admin'] = True
        else:
            data['anonymous'] = True

        return data
