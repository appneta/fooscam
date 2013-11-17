from flask import flash
from flask.ext.wtf import Form
from flask.ext.login import current_user
from wtforms import TextField, IntegerField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError
from werkzeug import check_password_hash

from foosweb.models import Player, Team

import pdb

class TeamupForm(Form):
    team_name = TextField('Team Name', validators = [DataRequired(message='Please enter a team name')])

    def validate_team_name(self, team_name):
        name_check = Team.query.filter(Team.name == team_name.data).first()

        if name_check is not None:
            raise ValidationError("Sorry, there's already a team called %s" % (team_name.data))

    def validate_invite(self, from_id, to_id):
        if from_id == to_id:
            flash('One is the loneliest number ...')
            return

        from_player = Player.query.filter(Player.id == from_id).first()
        to_player = Player.query.filter(Player.id == to_id).first()

        if to_player is None:
            flash('Invalid player ID', 'alert-danger')
            return

        team_check1 = Team.query.filter(Team.player_one == from_id).filter(Team.player_two == to_id).all()
        team_check2 = Team.query.filter(Team.player_one == to_id).filter(Team.player_two == from_id).all()

        for team in [team_check2, team_check1]:
            if len(team) > 0:
                if team[0].status == Team.STATUS_COMPLETE:
                    flash('You and %s are already team %s.' % (to_player.name, team[0].name), 'alert-danger')
                    return
                if team[0].status == Team.STATUS_PENDING:
                    flash('A team invite is pending between you and %s, it must be accepted or cancelled before you can send another.' % (to_player.name), 'alert-danger')
                    return
        return True
