from flask.ext.wtf import Form
from wtforms import TextField, IntegerField
from wtforms.validators import DataRequired, EqualTo
from gettext import gettext
import pdb

#TODO: move validators in here
class LoginForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address."))])
    password = TextField('password', validators = [DataRequired(message=gettext("Enter your password."))])

class TeamupForm(Form):
    team_name = TextField('Team Name', validators = [DataRequired(message=gettext("Please enter a team name"))])

class RequestResetForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address."))])

class SettingsForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Change your email address"))])
    password = TextField('password')
    confirm_pass = TextField('confirm_pass', validators = [EqualTo('password', message=gettext("Passwords must match"))])

class SignupForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address"))])
    name = TextField('name', validators = [DataRequired(message=gettext("Enter your name"))])
    password = TextField('password')
    confirm_pass = TextField('confirm_pass', validators = [EqualTo('password', message=gettext("Passwords must match"))])
