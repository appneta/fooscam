from flask.ext.wtf import Form
from wtforms import TextField, IntegerField
from wtforms.validators import DataRequired
from gettext import gettext
import pdb

class LoginForm(Form):
    email = TextField('email', description={'default': 'email'}, validators = [DataRequired(message=gettext("Enter your email address."))])
    password = TextField('password', validators = [DataRequired(message=gettext("Enter your password."))])

class TeamupForm(Form):
    team_name = TextField('Team Name', validators = [DataRequired(message=gettext("Please enter a team name"))])
