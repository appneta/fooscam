from foosweb.app import db
from foosweb.models import Player, Game, Team
from foosweb.controllers.base import BaseData
from foosweb.forms.player import  SignupForm, SettingsForm
from foosweb.gamewatch import GameWatch

from flask.ext.login import current_user
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime, timedelta
from hashlib import md5
import pdb

#TODO: game state controller

class PlayerData():
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


    def _get_teams_by_player_id(self, id):
        teams = Team.query.filter((Team.player_one == id) | (Team.player_two == id)).\
            filter(Team.status < Team.STATUS_DECLINED).all()

        retvals = []

        for team in teams:
            p_one_name = self._get_name_by_id(team.player_one)
            p_two_name = self._get_name_by_id(team.player_two)
            retvals.append((team.player_one, p_one_name, team.player_two, p_two_name, team.name, team.status))

        return retvals

    def GetCurrentPlayerGravatarURLs(self):
        gw = GameWatch()
        urls = gw.CurrentPlayerIDs()
        urls['bo'] = self._get_gravatar_url_by_id(urls['bo'])
        urls['bd'] = self._get_gravatar_url_by_id(urls['bd'])
        urls['ro'] = self._get_gravatar_url_by_id(urls['ro'])
        urls['rd'] = self._get_gravatar_url_by_id(urls['rd'])
        return urls

    def GetCurrentPlayerNames(self):
        gw = GameWatch()
        ids = gw.CurrentPlayerIDs()
        ids['bo'] = self._get_name_by_id(ids['bo'])
        ids['bd'] = self._get_name_by_id(ids['bd'])
        ids['ro'] = self._get_name_by_id(ids['ro'])
        ids['rd'] = self._get_name_by_id(ids['rd'])
        return ids

    def GetAllPlayersData(self):
        data = {}
        data['all_players'] = []
        all_players = Player.query.all()

        for player in all_players:
            if player.id != -1 and player.name != 'Guest':
                data['all_players'].append((player.id, player.name, self._get_gravatar_url_by_id(player.id, size=200)))

        base_data = BaseData.GetBaseData()

        return dict(data.items() + base_data.items())

    def GetProfileData(self, profile_id):
        """Get profile data for id and show it to user_id"""
        profile = {}
        profile['ro_wins'] = Game.query.filter(Game.red_off == profile_id).filter(Game.winner == 'red').count()
        profile['rd_wins'] = Game.query.filter(Game.red_def == profile_id).filter(Game.winner == 'red').count()
        profile['bo_wins'] = Game.query.filter(Game.blue_off == profile_id).filter(Game.winner == 'blue').count()
        profile['bd_wins'] = Game.query.filter(Game.blue_def == profile_id).filter(Game.winner == 'blue').count()

        profile['profile_name'] = self._get_name_by_id(profile_id)
        profile['profile_id'] = profile_id
        profile['gravatar_url'] = self._get_gravatar_url_by_id(profile_id)
        profile['hist_url'] = '/history/livehistjson/' + str(profile_id)
        profile['total_games'] = self.GetHistory(id=profile_id, count=True)
        profile['teams'] = self._get_teams_by_player_id(profile_id)

        base_data = BaseData.GetBaseData()

        return dict(profile.items() + base_data.items())

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

    def GetHistory(self,id=None, formatted=False, count=False):
        game_history = []
        if id is not None:
            if count:
                return Game.query.filter(\
                        (Game.red_off == id) | (Game.red_def == id) | (Game.blue_off == id) | (Game.blue_def == id)).\
                        order_by(Game.id).count()
            else:
                for game in Game.query.filter(\
                        (Game.red_off == id) | (Game.red_def == id) | (Game.blue_off == id) | (Game.blue_def == id)).\
                        order_by(Game.id):
                    game_history.append(game)
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
