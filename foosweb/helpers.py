from flask import redirect, url_for
from flask.ext.login import current_user
from flask.ext.wtf import Form
from wtforms import TextField, IntegerField
from wtforms.validators import DataRequired, ValidationError, EqualTo

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import logging
import collections
from gettext import gettext
from functools import wraps
from pprint import pprint

from hashlib import md5

from foosweb import PlayerData
from models import Player, Admin, Team

import pdb

log = logging.getLogger('gamewatch')

class Auth():
    def __init__(self):
        db = create_engine('sqlite:///foosball.db')
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()

    def _is_admin(self, id):
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

    def RequiresAdmin(self, func):
        """decorator to protect views to admins only"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated():
                if self._is_admin(current_user.id):
                    return func(*args, **kwargs)
            return redirect(url_for('home'))
        return wrapper

class LoginForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address."))])
    password = TextField('password', validators = [DataRequired(message=gettext("Enter your password."))])

class TeamupForm(Form):
    team_name = TextField('Team Name', validators = [DataRequired(message=gettext("Please enter a team name"))])

class TeamData():
    def __init__(self):
        db = create_engine('sqlite:///foosball.db')
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()

        self.pd = PlayerData()

    def TeamList(self):
        teams = self.session.query(Team).all()

        #TODO: add standings data & gravatar for teams
        #XXX: Split game data out of player data!
        retvals = []
        for team in teams:
            p_one_name = self.pd._get_name_by_id(team.player_one)
            p_two_name = self.pd._get_name_by_id(team.player_two)
            retvals.append((team.player_one, p_one_name, team.player_two, p_two_name, team.id, team.name))

        return retvals

    def ValidateInvite(self, from_player=-1, to_player=-1, team_name=''):
        #sanity
        auth = Auth()
        if (auth.GetPlayerByID(from_player) is None or auth.GetPlayerByID(to_player) is None):
            return
        try:
            team_check1 = self.session.query(Team).filter(Team.player_one == from_player).filter(Team.player_two == to_player).all()
            team_check2 = self.session.query(Team).filter(Team.player_one == to_player).filter(Team.player_two == from_player).all()
        except Exception, e:
            log.error('Something horrible happened trying to verify teams for p_id %s & p_id %s' % (from_player, to_player))
            return

        if team_check1 or team_check2:
            return "You and %s are already a team!" % (self.pd._get_name_by_id(to_player))

        try:
            name_check = self.session.query(Team).filter(Team.name == team_name).all()
        except Exception, e:
            log.error('Something horrible happened trying to verify team name %s' % (team_name))
            return

        if name_check:
            return "Sorry, there's already a team called %s" % (team_name)

    def SendInvite(self, from_player=-1, to_player=-1, team_name=''):
        team = Team(from_player, to_player, team_name)
        self.session.add(team)
        #TODO: global db session? wrap commit() for table locks
        self.session.commit()
        return True

    def GetInvitesFor(self, id):
        try:
            invites = self.session.query(Team).filter(Team.status == Team.STATUS_PENDING).\
                filter((Team.player_one == id) | (Team.player_two == id)).all()
        except Exception, e:
            log.error('something horrible happened whily trying to find invites for id %s' % (str(id)))
            return

        retvals = []
        for invite in invites:
            p_one_name = self.pd._get_name_by_id(invite.player_one)
            p_two_name = self.pd._get_name_by_id(invite.player_two)
            retvals.append((invite.player_one, p_one_name, invite.player_two, p_two_name, invite.name, invite.id))

        return retvals

    def AcceptInvite(self, invite_id, user_id):
        try:
            invite = self.session.query(Team).filter(Team.id == invite_id).filter(Team.status == Team.STATUS_PENDING).one()
        except Exception, e:
            log.error('soemthing horrible happened while trying to RSVP to invite id %s' % (str(invite_id)))
            return

        if invite.player_two == user_id:
            invite.status = Team.STATUS_COMPLETE
            self.session.add(invite)
            self.session.commit()
            return True

    def DeclineInvite(self, invite_id, user_id):
        try:
            invite = self.session.query(Team).filter(Team.id == invite_id).filter(Team.status == Team.STATUS_PENDING).one()
        except Exception, e:
            log.error('soemthing horrible happened while trying to RSVP to invite id %s' % (str(invite_id)))
            return

        if invite.player_two == user_id:
            invite.status = Team.STATUS_DECLINED
            self.session.add(invite)
            self.session.commit()
            return True
        elif invite.player_one == user_id:
            invite.status = Team.STATUS_CANCELLED
            self.session.add(invite)
            self.session.commit()
            return True

class RenderData():
    """base data to customize views for current user"""
    menu_items = (('Home', '/'), ('Players', '/players'), ('Teams', '/teams'), ('History', '/history'), ('Readme', '/readme'))

    def __init__(self):
        self.auth = Auth()

    def Get(self, user):
        data = {}
        data['menu'] = self.menu_items
        if user.is_authenticated():
            data['user_name'] = user.name
            data['user_id'] = user.id
            if self.auth._is_admin(user.id):
                data['admin'] = True
        else:
            data['anonymous'] = True
            data['id'] = -1

        return data

class SendMail():
    #Server name: smtp.office365.com
    #Port: 587
    #Encryption method: TLS
    def __init__():
        pass
