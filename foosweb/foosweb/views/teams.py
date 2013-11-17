from flask import Blueprint, request, flash, session, redirect, url_for, g
from flask.ext.login import login_required, current_user

from foosweb.controllers.team import TeamData
from foosweb.forms.team import TeamupForm
from foosweb.utils import render_pretty


mod = Blueprint('teams', __name__, url_prefix='/teams')

import pdb
import logging

log = logging.getLogger(__name__)

@mod.route('/')
def index():
    g.menu_item = 'Teams'
    td = TeamData()
    data = td.GetTeamsData()
    return render_pretty('teamlist.html', **data)

#TODO: individual team view
def team_by_id(self, team_id):
    return str(team_id)

@mod.route('/teamup/<int:teamup_with_id>', methods=['GET'])
@login_required
def show_teamup_form(teamup_with_id):
    td = TeamData()
    data = td.GetTeamupData(teamup_with_id)
    return render_pretty('teamup.html', **data)

@mod.route('/teamup/<int:teamup_with_id>', methods=['POST'])
@login_required
def process_teamup_form(teamup_with_id):
    td = TeamData()
    data = td.GetTeamupData(teamup_with_id)
    teamup_form = TeamupForm(request.form)
    if teamup_form.validate() and teamup_form.validate_invite(current_user.id, teamup_with_id):
        if td.SendInvite(from_player=current_user.id, to_player=teamup_with_id, team_name=teamup_form.team_name.data):
            flash('%s has been invited to join you on team %s!' % (data['profile_name'], teamup_form.team_name.data), 'alert-success')
        else:
            flash('Error sending invite!', 'alert-danger')
        return redirect(url_for('foos.index'))
    else:
        data['teamup_form'] = teamup_form
        return render_pretty('teamup.html', **data)

@mod.route('/teamup/invites')
@login_required
def invites():
    td = TeamData()
    data = td.GetInvitesData()
    return render_pretty('teamup_invites.html', **data)

@mod.route('/teamup/accept/<int:invite_id>')
@login_required
def teamup_accept_invite(invite_id):
    td = TeamData()
    if td.AcceptInvite(invite_id, current_user.id):
        flash('You dun teamed up!', 'alert-success')
    else:
        flash('Error accepting invite!', 'alert-danger')
    return redirect(request.referrer or url_for('foos.index'))

@mod.route('/teamup/decline/<int:invite_id>')
@login_required
def teamup_decline_invite(invite_id):
    td = TeamData()
    if td.DeclineInvite(invite_id, current_user.id):
        flash('Invite cancelled.', 'alert-warning')
    return redirect(request.referrer or url_for('foos.index'))
