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
from models import Player

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
        return player

class LoginForm(Form):
    #TODO: figure out how the hell to get these error messages to display!
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address."))])
    password = TextField('password', validators = [DataRequired(message=gettext("Enter your password."))])
    auth = Auth()

    """def validate(self):
        if self.auth.Login(email=self.email.data, password=self.password.data) is not None:
            return True"""


class Menu():
    menu_items = [{'name': 'Home', 'url': '/'}, \
             {'name': 'History', 'url': '/history'}, \
             {'name': 'Readme', 'url': '/readme'}]

    def __init__(self, user, entry=None):
        self.entry = entry
        self.menu = {}
        self.menu['menu'] = (item for item in self.menu_items if item['name'] != entry)
        if user.is_authenticated():
            self.menu['name'] = user.name
            self.menu['id'] = user.id
        else:
            self.menu['anonymous'] = True

    def Make(self):
        return collections.OrderedDict(sorted(self.menu.items()))
