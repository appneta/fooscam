from flask import flash
from flask.ext.wtf import Form
from flask.ext.login import current_user
from wtforms import TextField, IntegerField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError
from werkzeug import check_password_hash

from foosweb.models import Player

import pdb

class LoginForm(Form):
    email = TextField('Email address', validators = [DataRequired(), Email(message='Please enter a valid email address.')])
    password = PasswordField('Password', validators = [DataRequired()])

    def validate_login(self):
        email = str(self.email.data).strip().lower()
        player = Player.query.filter_by(email=email).first()
        if player is not None:
            if check_password_hash(player.password, self.password.data):
                return True

class RequestResetForm(Form):
    email = TextField('Email address', validators = [DataRequired(), Email(message='Please enter a valid email address.')])

class SettingsForm(Form):
    email = TextField('Email address', validators = [DataRequired(message='Change your email address.'), Email(message='Please enter a valid email address.')])
    password = PasswordField('Password')
    confirm_pass = PasswordField('Confirm password', validators = [ \
        DataRequired('Confirm your new password'),
        EqualTo('password', message='Passwords must match')])

    def validate_email(self, email):
        check = Player.query.filter(Player.email == email.data).first()
        if check is not None:
            if check.id != current_user.id:
                raise ValidationError('An account with that email address already exists.')

class SignupForm(Form):
    name = TextField('Name', validators = [DataRequired(message='Enter your name')])
    email = TextField('Email address', validators = [DataRequired(message='Change your email address.'), Email(message='Please enter a valid email address.')])
    password = PasswordField('Password', [DataRequired(message='You must create a password')])
    confirm_pass = PasswordField('Confirm password', validators = [ \
        DataRequired('Confirm your new password'),
        EqualTo('password', message='Passwords must match')])

    def validate_name(self, name):
        check = Player.query.filter(Player.name == name.data).first()

        if check is not None:
            raise ValidationError('A player by that name is already registered, please choose another name')

    def validate_email(self, email):
        check = Player.query.filter(Player.email == email.data.lower()).first()

        if check is not None:
            raise ValidationError('An player with that email address already exists.')
