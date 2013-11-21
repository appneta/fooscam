from foosweb.app import db
from foosweb.models import Player, Game, Team
from foosweb.controllers.base import BaseData
from foosweb.forms.player import  SignupForm, SettingsForm

from flask import g
from flask.ext.login import current_user
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime, timedelta
from hashlib import md5
import pdb

#TODO: game state controller

class PlayerData():

    def __init__(self):
        #if current_players global is not set during this request, fill it in with -1 (anon/none player)
        if g.get('current_players', None) is None:
            g.current_players = {'bo': -1, 'bd': -1, 'ro': -1, 'rd': -1}

    def _tidy_sa_results(self, result):
        retvals = []
        for item in result:
            if type(item[0]) == unicode:
                retvals.append(str(item[0]))
            else:
                retvals.append(item[0])
        return retvals

    def _get_email_by_id(self, player_id):
        if player_id == -1:
            return
        else:
            email = Player.query.with_entities(Player.email).filter(Player.id == player_id).first()
            if email is not None:
                return email[0]

    def _get_gravatar_url_by_id(self, id, size=80):
        email = self._get_email_by_id(id)
        if email is not None:
            email = email.strip().lower()
            g_hash = md5(email).hexdigest()
            return 'http://gravatar.com/avatar/%s?s=%s' % (g_hash, int(size))
        else:
             return ''

    def _get_name_by_id(self, player_id):
        if player_id == -1:
            player_name = 'None'
        else:
            player_name = Player.query.with_entities(Player.name).filter_by(id=player_id).first()
            if player_name is not None:
                player_name = player_name[0]
            else:
                player_name = 'Anonymous'

        return player_name


    def _get_current_teams_by_player_id(self, id):
        teams = Team.query.filter((Team.player_one == id) | (Team.player_two == id)).\
            filter(Team.status == Team.STATUS_COMPLETE).all()

        retvals = []

        for team in teams:
            p_one_name = self._get_name_by_id(team.player_one)
            p_two_name = self._get_name_by_id(team.player_two)
            retvals.append((team.player_one, p_one_name, team.player_two, p_two_name, team.name, team.id))

        return retvals

    def GetCurrentPlayerGravatarURLs(self):
        urls = {}
        urls['bo'] = self._get_gravatar_url_by_id(g.current_players['bo'])
        urls['bd'] = self._get_gravatar_url_by_id(g.current_players['bd'])
        urls['ro'] = self._get_gravatar_url_by_id(g.current_players['ro'])
        urls['rd'] = self._get_gravatar_url_by_id(g.current_players['rd'])
        return urls

    def GetCurrentPlayerNames(self):
        names = {}
        names['bo'] = self._get_name_by_id(g.current_players['bo'])
        names['bd'] = self._get_name_by_id(g.current_players['bd'])
        names['ro'] = self._get_name_by_id(g.current_players['ro'])
        names['rd'] = self._get_name_by_id(g.current_players['rd'])
        return names

    def GetAllPlayersData(self):
        data = {}
        data['all_players'] = []
        all_players = Player.query.all()

        for player in all_players:
            if player.id != -1 and player.name != 'Guest':
                data['all_players'].append((player.id, player.name, self._get_gravatar_url_by_id(player.id, size=200)))

        base_data = BaseData.GetBaseData()

        return dict(data.items() + base_data.items())

    def GetPublicProfileData(self, profile_id):
        """Get profile data for id and show it to user_id"""
        profile = {}
        profile['ro_wins'] = Game.query.filter(Game.red_off == profile_id).filter(Game.winner == 'red').count()
        profile['rd_wins'] = Game.query.filter(Game.red_def == profile_id).filter(Game.winner == 'red').count()
        profile['bo_wins'] = Game.query.filter(Game.blue_off == profile_id).filter(Game.winner == 'blue').count()
        profile['bd_wins'] = Game.query.filter(Game.blue_def == profile_id).filter(Game.winner == 'blue').count()

        profile['profile_name'] = self._get_name_by_id(profile_id)
        profile['profile_id'] = profile_id
        profile['gravatar_url'] = self._get_gravatar_url_by_id(profile_id, size=250)
        profile['hist_url'] = '/history/livehistjson/' + str(profile_id)
        profile['total_games'] = self.GetHistory(player_id=profile_id, count=True)
        profile['teams'] = self._get_current_teams_by_player_id(profile_id)

        base_data = BaseData.GetBaseData()

        return dict(profile.items() + base_data.items())


    """def GetMyProfileData(self, profile_id):
        profile = self.GetPublicProfileData(profile_id)
        td = TeamData()
        invites_dict = TeamData.GetInvitesData()

        return dict(profile.items() + invites_dict())"""

    def GetSettingsData(self):
        settings = {}
        settings['settings_form'] = SettingsForm()

        settings['settings_form'].email.data = self._get_email_by_id(current_user.id)
        base_data = BaseData.GetBaseData()

        return dict(settings.items() + base_data.items())

    def SetSettingsData(self, settings_form, current_player):
        #return true if data has actually changed
        changed = False
        if current_player.email != settings_form.email.data:
            if current_player.email != settings_form.email.data:
                changed = True
                current_player.email = settings_form.email.data

        if settings_form.password.data != '':
            if settings_form.password.data == settings_form.confirm_pass.data:
                if not check_password_hash(settings_form.password.data, current_player.password):
                    changed = True
                    current_player.password = generate_password_hash(settings_form.password.data, method='pbkdf2:sha256:10000')

        if changed:
            db.session.add(current_player)
            db.session.commit()

        return changed

    @classmethod
    def GetSignupData(self):
        base_data = BaseData.GetBaseData()
        base_data['signup_form'] = SignupForm()
        return base_data

    def AddNewPlayer(self, signup_form):
        hashed_pass = generate_password_hash(signup_form['password'], method='pbkdf2:sha256:10000')
        new_player = Player(signup_form['name'], signup_form['email'], hashed_pass)
        db.session.add(new_player)
        db.session.commit()
        return new_player

    def GetHistory(self, player_id=None, formatted=False, count=False, team_id=None):
        #TODO: split collecting games to report and formatting of game history
        game_history = []

        if player_id is not None and team_id is not None:
            raise ValueError('GetHistory accepts one player or one team, but not both!')

        if player_id is not None:
            #single player game count
            if count:
                return Game.query.filter(\
                        (Game.red_off == player_id) | (Game.red_def == player_id) | (Game.blue_off == player_id) | (Game.blue_def == player_id)).\
                        order_by(Game.id).count()
            #single player game stats
            else:
                for game in Game.query.filter(\
                        (Game.red_off == player_id) | (Game.red_def == player_id) | (Game.blue_off == player_id) | (Game.blue_def == player_id)).\
                        order_by(Game.id):
                    game_history.append(game)
        elif team_id is not None:
            #team stats
            team = Team.query.filter(Team.id == team_id).first()
            if team is None:
                return

            team_ids = [team.player_one, team.player_two]

            blue_games = Game.query.filter(Game.blue_off.in_(team_ids)).filter(Game.blue_def.in_(team_ids)).all()
            red_games = Game.query.filter(Game.red_off.in_(team_ids)).filter(Game.red_def.in_(team_ids)).all()
            for game in (blue_games +  red_games):
                game_history.append(game)

        #all players game stats
        else:
            for game in Game.query.order_by(Game.id):
                game_history.append(game)

        if formatted:
            retvals = []
            for game in game_history:
                game_duration = datetime.fromtimestamp(game.ended) - datetime.fromtimestamp(game.started)
                ro = "<a href='/players/%s'>%s</a>" % (game.red_off, self._get_name_by_id(game.red_off))
                rd = "<a href='/players/%s'>%s</a>" % (game.red_def, self._get_name_by_id(game.red_def))
                bo = "<a href='/players/%s'>%s</a>" % (game.blue_off, self._get_name_by_id(game.blue_off))
                bd = "<a href='/players/%s'>%s</a>" % (game.blue_def, self._get_name_by_id(game.blue_def))
                retvals.append([ro, rd, bo, bd,
                    game.red_score, game.blue_score, \
                    datetime.fromtimestamp(game.started).strftime('%Y-%m-%d %H:%M:%S'), \
                    datetime.fromtimestamp(game.ended).strftime('%Y-%m-%d %H:%M:%S'), \
                    str(timedelta(seconds=game_duration.seconds)), \
                    game.winner])
            return retvals
        else:
            return game_history
