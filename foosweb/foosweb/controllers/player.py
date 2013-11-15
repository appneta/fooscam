from foosweb.app import db
from foosweb.models.player import Player
from foosweb.controllers.base import BaseData
from foosweb.forms.player import  SignupForm
from werkzeug.security import generate_password_hash

from hashlib import md5
import pdb

import logging
log = logging.getLogger(__name__)

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
            try:
                return str(self.session.query(Player.email).filter_by(id=player_id).one()[0])
            except NoResultFound:
                return

    def _get_gravatar_url_by_id(self, id, size=80):
        email = self._get_email_by_id(id)
        if email is not None:
            email = email.strip().lower()
            g_hash = md5(email).hexdigest()
            return 'http://gravatar.com/avatar/%s?s=%s' % (g_hash, int(size))
        else:
             return ''

    def _player_gravatar_url(self, player, size=80):
        g_hash = md5(player.email).hexdigest()
        return 'http://gravatar.com/avatar/%s?s=%s' % (g_hash, int(size))

    def _make_gravatar_url(self, email, size=80):
        if email is not None:
            return 'http://gravatar.com/avatar/%s?s=%s' % md5(email.strip().lower()).hexdigest(), int(size)

    def GetNameByID(self, player_id):
        if player_id == -1:
            player_name = 'None'
        else:
            try:
                player_name = str(self.session.query(Player.name).filter_by(id=player_id).one()[0])
            except NoResultFound:
                player_name = 'Anonymous'

        return player_name


    def _get_teams_by_player_id(self, id):
        try:
            teams = self.session.query(Team).filter((Team.player_one == id) | (Team.player_two == id)).\
            filter(Team.status < Team.STATUS_DECLINED).all()
        except Exception, e:
            log.debug('Something horrible happened trying to find teams for player: %s' % (str(id)))
            return

        retvals = []

        for team in teams:
            p_one_name = self.GetNameByID(team.player_one)
            p_two_name = self.GetNameByID(team.player_two)
            retvals.append((team.player_one, p_one_name, team.player_two, p_two_name, team.name, team.status))

        return retvals

    def GetGravatarURLs(self, id):
        """get url if id=INT, if id is a dict of current players populate with urls"""
        if type(id) == int:
            return self._get_gravatar_url_by_id(id)
        elif type(id) == dict:
            id['bo'] = self._get_gravatar_url_by_id(id['bo'])
            id['bd'] = self._get_gravatar_url_by_id(id['bd'])
            id['ro'] = self._get_gravatar_url_by_id(id['ro'])
            id['rd'] = self._get_gravatar_url_by_id(id['rd'])
            return id

    def GetNames(self, id=None):
        """get all names by default (id==None), get one name if id=INT, if id is a dict of current players populate with names"""
        if id is None:
            player_names = self.session.query(Player.name).all()
            return self._tidy_sa_results(player_names)

        if type(id) == int:
            if id == -1:
                return 'None'
            else:
                return self.GetNameByID(id)

        if type(id) == dict:
            id['bo'] = self.GetNameByID(id['bo'])
            id['bd'] = self.GetNameByID(id['bd'])
            id['ro'] = self.GetNameByID(id['ro'])
            id['rd'] = self.GetNameByID(id['rd'])
            return id

    def GetAllPlayersData(self):
        data = {}
        data['all_players'] = []
        all_players = Player.query.all()

        for player in all_players:
            if player.id != -1 and player.name != 'Guest':
                data['all_players'].append((player.id, player.name, self._player_gravatar_url(player, size=200)))

        base_data = BaseData.GetBaseData()

        return dict(data.items() + base_data.items())

    def GetProfileData(self, current_user, current_view, profile_id):
        """Get profile data for id and show it to user_id"""
        profile = {}
        try:
            profile['ro_wins'] = self.session.query(Game).filter(Game.red_off == profile_id).filter(Game.winner == 'red').count()
            profile['rd_wins'] = self.session.query(Game).filter(Game.red_def == profile_id).filter(Game.winner == 'red').count()
            profile['bo_wins'] = self.session.query(Game).filter(Game.blue_off == profile_id).filter(Game.winner == 'blue').count()
            profile['bd_wins'] = self.session.query(Game).filter(Game.blue_def == profile_id).filter(Game.winner == 'blue').count()
        except Exception, e:
            log.error('Failed to get wins from db for id %s with error %s' % (str(id), repr(e)))
            return

        profile['profile_name'] = self.GetNameByID(profile_id)
        profile['profile_id'] = profile_id
        profile['gravatar_url'] = self._get_gravatar_url_by_id(profile_id)
        profile['hist_url'] = '/playerhistjson/' + str(profile_id)
        profile['total_games'] = self.GetHistory(id=profile_id, count=True)
        profile['teams'] = self._get_teams_by_player_id(profile_id)

        base_data = self.bd.GetBaseData(current_user, current_view)

        return dict(profile.items() + base_data.items())

    def GetSettingsData(self, current_user, current_view):
        settings = {}
        settings['settings_form'] = SettingsForm()

        settings['settings_form'].email.data = self._get_email_by_id(current_user.id)
        base_data = self.bd.GetBaseData(current_user, current_view)

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
                if not check_hash(settings_form.password.data, current_player.password):
                    changed = True
                    current_player.password = make_hash(settings_form.password.data)

        if changed:
            self.session.add(current_player)
            self.session.commit()

        return changed

    @classmethod
    def GetSignupData(self):
        base_data = BaseData.GetBaseData()
        base_data['signup_form'] = SignupForm()
        return base_data

    def AddNewPlayer(self, signup_form):
        hashed_pass = generate_password_hash(signup_form['password'])
        new_player = Player(signup_form['name'], signup_form['email'], hashed_pass)
        db.session.add(new_player)
        db.session.commit()
        return new_player

    def GetHistory(self,id=None, formatted=False, count=False):
        game_history = []
        if id is not None:
            if count:
                return self.session.query(Game).filter(\
                        (Game.red_off == id) | (Game.red_def == id) | (Game.blue_off == id) | (Game.blue_def == id)).\
                        order_by(Game.id).count()
            else:
                for game in self.session.query(Game).filter(\
                        (Game.red_off == id) | (Game.red_def == id) | (Game.blue_off == id) | (Game.blue_def == id)).\
                        order_by(Game.id):
                    game_history.append(game)
        else:
            for game in self.session.query(Game).order_by(Game.id):
                game_history.append(game)

        if formatted:
            retvals = []
            for game in game_history:
                game_duration = datetime.fromtimestamp(game.ended) - datetime.fromtimestamp(game.started)
                ro = "<a href='/players/%s'>%s</a>" % (game.red_off, self.GetNameByID(game.red_off))
                rd = "<a href='/players/%s'>%s</a>" % (game.red_def, self.GetNameByID(game.red_def))
                bo = "<a href='/players/%s'>%s</a>" % (game.blue_off, self.GetNameByID(game.blue_off))
                bd = "<a href='/players/%s'>%s</a>" % (game.blue_def, self.GetNameByID(game.blue_def))
                retvals.append([ro, rd, bo, bd,
                    game.red_score, game.blue_score, \
                    datetime.fromtimestamp(game.started).strftime('%Y-%m-%d %H:%M:%S'), \
                    datetime.fromtimestamp(game.ended).strftime('%Y-%m-%d %H:%M:%S'), \
                    str(timedelta(seconds=game_duration.seconds)), \
                    game.winner])
            return retvals
        else:
            return game_history
