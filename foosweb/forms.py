from flask import flash
from flask.ext.wtf import Form
from wtforms import TextField, IntegerField
from wtforms.validators import DataRequired, EqualTo, ValidationError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from gettext import gettext
from models import Player, Team
from ssapin_crypt import check_hash
from db import get_db_session

import logging
import pdb

log = logging.getLogger('gamewatch')

class LoginForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address."))])
    password = TextField('password', validators = [DataRequired(message=gettext("Enter your password."))])

    def validate_login(self):
        email = str(self.email.data).strip().lower()
        session = get_db_session()
        try:
            player = session.query(Player).filter_by(email=email).one()
        except NoResultFound:
            return

        if check_hash(self.password.data, player.password):
            return True

class TeamupForm(Form):
    team_name = TextField('Team Name', validators = [DataRequired(message=gettext("Please enter a team name"))])

    def validate_team_name(self, team_name):
        session = get_db_session()

        try:
            name_check = session.query(Team).filter(Team.name == team_name.data).all()
        except Exception, e:
            log.error('Exception %s thrown while trying to validate team name %s' % (repr(e), team_name.data))
            return

        if len(name_check) != 0:
            raise ValidationError("Sorry, there's already a team called %s" % (team_name.data))

    def validate_invite(self, from_id, to_id):
        if from_id == to_id:
            flash('One is the loneliest number ...')
            return

        session = get_db_session()

        try:
            session.query(Player).filter(Player.id == from_id).one()
            to_player = session.query(Player).filter(Player.id == to_id).one()
        except NoResultFound:
            flash('Invalid player ID', 'alert-danger')
            return
        except MultipleResultsFound:
            log.error('Player table has multiple players with the same name!')
            return
        except Exception, e:
            log.error('Exception %s raised while trying to verify player ids %s and %s' % (repr(e), str(from_id), str(to_id)))
            return

        try:
            team_check1 = session.query(Team).filter(Team.player_one == from_id).filter(Team.player_two == to_id).all()
            team_check2 = session.query(Team).filter(Team.player_one == to_id).filter(Team.player_two == from_id).all()
        except MultipleReultsFound:
            log.error('Players %s and %s have multiple teams!')
            return
        except Exception, e:
            log.error('Exception %s raised while trying to verify teams for player ids %s and  %s' % (repr(e), str(from_id), str(to_id)))
            return

        for team in [team_check2, team_check1]:
            if len(team) > 0:
                if team[0].status == Team.STATUS_COMPLETE:
                    flash('You and %s are already team %s.' % (to_player.name, team[0].name), 'alert-danger')
                    return
                if team[0].status == Team.STATUS_PENDING:
                    flash('A team invite is pending between you and %s, it must be accepted or cancelled before you can send another.' % (to_player.name), 'alert-danger')
                    return
        return True

class RequestResetForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address."))])

    def validate_email(self, email):

        if email.data.find('@') < 0:
            raise ValidationError("That sorta doesn't look like an email address ...")

class SettingsForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Change your email address"))])
    password = TextField('password')
    confirm_pass = TextField('confirm_pass', validators = [EqualTo('password', message=gettext("Passwords must match"))])

    def validate_email(self, email):

        if email.data.find('@') < 0:
            raise ValidationError("That sorta doesn't look like an email address ...")

        self.session = get_db_session()
        check = None
        try:
            check = self.session.query(Player).filter(Player.email == email.data).all()
        except Exception, e:
            log.error('Exception %s thrown trying to validate new player email %s' % (repr(e), email.data))

        if check is not None:
            if len(check) > 0:
                raise ValidationError('An account with that email address already exists.')

class SignupForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address"))])
    name = TextField('name', validators = [DataRequired(message=gettext("Enter your name"))])
    password = TextField('password')
    confirm_pass = TextField('confirm_pass', validators = [EqualTo('password', message=gettext("Passwords must match"))])

    def validate_name(self, name):
        self.session = get_db_session()
        check = None
        try:
            check = self.session.query(Player).filter(Player.name == name.data).all()
        except Exception, e:
            log.error('Exception %s thrown trying to validate new player name %s' % (repr(e), name.data))

        if check is not None:
            if len(check) > 0:
                raise ValidationError('A player by that name is already registered, please choose another name')

    def validate_email(self, email):

        if email.data.find('@') < 0:
            raise ValidationError("That sorta doesn't look like an email address ...")

        self.session = get_db_session()
        check = None
        try:
            check = self.session.query(Player).filter(Player.email == email.data).all()
        except Exception, e:
            log.error('Exception %s thrown trying to validate new player email %s' % (repr(e), email.data))

        if check is not None:
            if len(check) > 0:
                raise ValidationError('An account with that email address already exists.')
