from foosweb.app import db
from foosweb.models import Game, Team
from foosweb.controllers.base import BaseData
from foosweb.controllers.player import PlayerData
from foosweb.forms.team import TeamupForm

from flask.ext.login import current_user
import pdb

import logging
log = logging.getLogger(__name__)

class TeamData():
    def __init__(self):
        self.pd = PlayerData()

    def _get_team_total_wins(self, team):
        try:
           red_games1 = self.session.query(Game).filter(Game.red_off == team.player_one).\
                filter(Game.red_def == team.player_two).\
                filter(Game.winner == 'red').count()
           red_games2 = self.session.query(Game).filter(Game.red_off == team.player_two).\
                filter(Game.red_def == team.player_one).\
                filter(Game.winner == 'red').count()
           blue_games1 = self.session.query(Game).filter(Game.blue_off == team.player_one).\
                filter(Game.blue_def == team.player_two).\
                filter(Game.winner == 'blue').count()
           blue_games2 = self.session.query(Game).filter(Game.blue_off == team.player_two).\
                filter(Game.blue_def == team.player_one).\
                filter(Game.winner == 'blue').count()
        except Exception, e:
            log.error('Exception %s occurred looking up games for team %s' % (repr(e), team.id))
            return

        return red_games1 + red_games2 + blue_games1 + blue_games2

    def GetTeamsData(self):
        teams = Team.query.filter(Team.status == Team.STATUS_COMPLETE).all()

        #TODO: add standings data & gravatar for teams
        retvals = {}
        retvals['teams'] = []
        for team in teams:
            p_one_name = self.pd._get_name_by_id(team.player_one)
            p_two_name = self.pd._get_name_by_id(team.player_two)
            team_total_wins = self._get_team_total_wins(team)
            retvals['teams'].append((team.player_one, p_one_name, team.player_two, p_two_name, team.id, team.name, team_total_wins))

        #sort teams by number of wins descending
        retvals['teams'].sort(key=lambda tup: tup[6], reverse=True)

        base_data = BaseData.GetBaseData()

        return dict(retvals.items() + base_data.items())

    def GetTeamupData(self, teamup_with_id):
        retvals = {}
        base_data = BaseData.GetBaseData()
        retvals['profile_name'] = self.pd._get_name_by_id(teamup_with_id)
        retvals['profile_id'] = teamup_with_id
        retvals['teamup_form'] = TeamupForm()

        return dict(retvals.items() + base_data.items())

    def SendInvite(self, from_player=-1, to_player=-1, team_name=''):
        team = Team(from_player, to_player, team_name)
        db.session.add(team)
        db.session.commit()
        return True

    def GetInvitesData(self):
        invites = Team.query.filter(Team.status == Team.STATUS_PENDING).\
            filter((Team.player_one == current_user.id) | (Team.player_two == current_user.id)).all()

        retvals = {}
        retvals['invites'] = []
        for invite in invites:
            p_one_name = self.pd._get_name_by_id(invite.player_one)
            p_two_name = self.pd._get_name_by_id(invite.player_two)
            retvals['invites'].append((invite.player_one, p_one_name, invite.player_two, p_two_name, invite.name, invite.id))

        base_data = BaseData.GetBaseData()

        return dict(retvals.items() + base_data.items())

    def AcceptInvite(self, invite_id, user_id):
        invite = Team.query.filter(Team.id == invite_id).filter(Team.status == Team.STATUS_PENDING).first()

        if invite is None:
            return

        if invite.player_two == user_id:
            invite.status = Team.STATUS_COMPLETE
            db.session.add(invite)
            db.session.commit()
            return True

    def DeclineInvite(self, invite_id, user_id):
        invite = Team.query.filter(Team.id == invite_id).filter(Team.status == Team.STATUS_PENDING).first()

        if invite is None:
            return

        if invite.player_two == user_id:
            invite.status = Team.STATUS_DECLINED
            db.session.add(invite)
            db.session.commit()
            return True

        elif invite.player_one == user_id:
            invite.status = Team.STATUS_CANCELLED
            db.session.add(invite)
            db.session.commit()
            return True