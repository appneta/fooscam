from flask.ext.wtf import Form
from wtforms import TextField, IntegerField
from wtforms.validators import DataRequired, EqualTo
from gettext import gettext
import pdb

#TODO: these errors stopped working again :/
class LoginForm(Form):
    email = TextField('email', validators = [DataRequired(message=gettext("Enter your email address."))])
    password = TextField('password', validators = [DataRequired(message=gettext("Enter your password."))])

class TeamupForm(Form):
    team_name = TextField('Team Name', validators = [DataRequired(message=gettext("Please enter a team name"))])

class PasswordResetForm(Form):
    password = TextField('password', validators = [DataRequired(message=gettext("Enter new password."))])
    confirm_pass = TextField('confirm_pass', validators = [EqualTo('password', message=gettext("Passwords must match"))])
