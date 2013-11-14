from flask import flash
from flask.ext.wtf import Form
from wtforms import TextField, IntegerField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError

import logging
import pdb

log = logging.getLogger('gamewatch')

class LoginForm(Form):
    email = TextField('Email address', validators = [DataRequired(), Email(message='Please enter a valid email address.')])
    password = PasswordField('Password', validators = [DataRequired()])

    def validate_login(self):
        email = str(self.email.data).strip().lower()
        session = get_db_session()
        try:
            player = session.query(Player).filter_by(email=email).one()
        except NoResultFound:
            return

        if check_hash(self.password.data, player.password):
            return True

class RequestResetForm(Form):
    email = TextField('Email address', validators = [DataRequired(), Email(message='Please enter a valid email address.')])

class SettingsForm(Form):
    email = TextField('Email address', validators = [DataRequired(message='Change your email address.'), Email(message='Please enter a valid email address.')])
    password = PasswordField('Password')
    confirm_pass = PasswordField('Confirm password', validators = [ \
        DataRequired('Confirm your new password'),
        EqualTo('Password', message='Passwords must match')])

    def validate_email(self, email):

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
    name = TextField('name', validators = [DataRequired(message='Enter your name')])
    email = TextField('Email address', validators = [DataRequired(message='Change your email address.'), Email(message='Please enter a valid email address.')])
    password = PasswordField('Password')
    confirm_pass = PasswordField('Confirm password', validators = [ \
        DataRequired('Confirm your new password'),
        EqualTo('Password', message='Passwords must match')])

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

        self.session = get_db_session()
        check = None
        try:
            check = self.session.query(Player).filter(Player.email == email.data).all()
        except Exception, e:
            log.error('Exception %s thrown trying to validate new player email %s' % (repr(e), email.data))

        if check is not None:
            if len(check) > 0:
                raise ValidationError('An account with that email address already exists.')
