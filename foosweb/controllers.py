from flask import redirect, url_for
from flask.ext.login import current_user
from flask.ext.mail import Message
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from datetime import datetime, timedelta
import os
from hashlib import md5
from ssapin_crypt import make_hash, check_hash #straight up jacked from https://github.com/SimonSapin/snippets/blob/master/hashing_passwords.py
from functools import wraps
from forms import LoginForm, TeamupForm, SettingsForm, SignupForm
from models import Player, Team, Game, Admin, PasswordReset
from db import get_db_session

import pdb

import logging
log = logging.getLogger('gamewatch')

#TODO: game state controller

class PlayerData():
    def __init__(self):
        self.session = get_db_session()
        self.bd = BaseData()

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

    def GetAllPlayersData(self, current_user, current_view):
        data = {}
        data['all_players'] = []
        all_players = self.session.query(Player).all()

        for player in all_players:
            if player.id != -1 and player.name != 'Guest':
                data['all_players'].append((player.id, player.name,  self._get_gravatar_url_by_id(player.id, size=200)))

        base_data = self.bd.GetBaseData(current_user, current_view)

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

    def GetSignupData(self, current_player, current_view):
        base_data = self.bd.GetBaseData(current_user, current_view)
        base_data['signup_form'] = SignupForm()

        return base_data

    def ValidateNewPlayer(self, signup_form):
        check = None
        if signup_form.name.data == '':
            return 'Please enter your name'
        else:
            try:
                check = self.session.query(Player).filter(Player.name == signup_form.name.data).all()
            except Exception, e:
                log.error('Exception %s thrown trying to validate new player name %s' % (repr(e), signup_form.name.data))

        if len(check) > 0:
            return 'A player by that name is already registered, please choose another name'

        if signup_form.email.data == '':
            return 'Please enter your email address'
        else:
            try:
                check = self.session.query(Player).filter(Player.email == signup_form.name.email).all()
            except Exception, e:
                log.error('Exception %s thrown trying to validate new player email %s' % (repr(e), signup_form.email.data))

        if len(check) > 0:
            return 'An account with that email address already exists, try a password reset?'

        if signup_form.password.data != '':
            if signup_form.password.data == signup_form.confirm_pass.data:
                hashed_pass = make_hash(signup_form.password.data)

        new_player = Player(signup_form.name.data, signup_form.email.data, hashed_pass)
        self.session.add(new_player)
        self.session.commit()
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

class TeamData():
    def __init__(self):
        self.session = get_db_session()
        self.pd = PlayerData()
        self.bd = BaseData()

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

    def GetTeamsData(self, current_user, current_view):
        teams = self.session.query(Team).filter(Team.status == Team.STATUS_COMPLETE).all()

        #TODO: add standings data & gravatar for teams
        retvals = {}
        retvals['teams'] = []
        for team in teams:
            p_one_name = self.pd.GetNameByID(team.player_one)
            p_two_name = self.pd.GetNameByID(team.player_two)
            team_total_wins = self._get_team_total_wins(team)
            retvals['teams'].append((team.player_one, p_one_name, team.player_two, p_two_name, team.id, team.name, team_total_wins))

        #sort teams by number of wins descending
        retvals['teams'].sort(key=lambda tup: tup[6], reverse=True)

        base_data = self.bd.GetBaseData(current_user, current_view)

        return dict(retvals.items() + base_data.items())

    def GetTeamupData(self, current_user, current_view, teamup_with_id):
        retvals = {}
        base_data = self.bd.GetBaseData(current_user, current_view)
        retvals['profile_name'] = self.pd.GetNameByID(teamup_with_id)
        retvals['profile_id'] = teamup_with_id
        retvals['teamup_form'] = TeamupForm()

        return dict(retvals.items() + base_data.items())

    def ValidateInvite(self, from_player=-1, to_player=-1, team_name=''):
        """return None if invite checks out, returns error message if not"""
        if from_player == to_player:
            return 'One is the loneliest number ...'

        if team_name == '' or team_name is None:
            return 'Gonna need to call yourselves something!'

        #sanity
        auth = Auth()
        if (auth.GetPlayerByID(from_player) is None or auth.GetPlayerByID(to_player) is None):
            return

        try:
            team_check1 = self.session.query(Team).filter(Team.player_one == from_player).filter(Team.player_two == to_player).all()
            team_check2 = self.session.query(Team).filter(Team.player_one == to_player).filter(Team.player_two == from_player).all()
        except Exception, e:
            log.error('Something horrible happened trying to verify teams for p_id %s & p_id %s' % (from_player, to_player))
            return

        #TODO: customize message to team status (Pending AND Cancelled)
        if team_check1 or team_check2:
            return "You and %s are already a team!" % (self.pd.GetNameByID(to_player))

        try:
            name_check = self.session.query(Team).filter(Team.name == team_name).all()
        except Exception, e:
            log.error('Something horrible happened trying to verify team name %s' % (team_name))
            return

        if name_check:
            return "Sorry, there's already a team called %s" % (team_name)

    def SendInvite(self, from_player=-1, to_player=-1, team_name=''):
        team = Team(from_player, to_player, team_name)
        self.session.add(team)
        self.session.commit()
        return True

    def GetInvitesData(self, current_user, current_view):
        try:
            invites = self.session.query(Team).filter(Team.status == Team.STATUS_PENDING).\
                filter((Team.player_one == current_user.id) | (Team.player_two == current_user.id)).all()
        except Exception, e:
            log.error('something horrible happened whily trying to find invites for id %s' % (str(current_user.id)))
            return

        retvals = {}
        retvals['invites'] = []
        for invite in invites:
            p_one_name = self.pd.GetNameByID(invite.player_one)
            p_two_name = self.pd.GetNameByID(invite.player_two)
            retvals['invites'].append((invite.player_one, p_one_name, invite.player_two, p_two_name, invite.name, invite.id))

        base_data = self.bd.GetBaseData(current_user, current_view)

        return dict(retvals.items() + base_data.items())

    def AcceptInvite(self, invite_id, user_id):
        try:
            invite = self.session.query(Team).filter(Team.id == invite_id).filter(Team.status == Team.STATUS_PENDING).one()
        except Exception, e:
            log.error('soemthing horrible happened while trying to RSVP to invite id %s' % (str(invite_id)))
            return

        if invite.player_two == user_id:
            invite.status = Team.STATUS_COMPLETE
            self.session.add(invite)
            self.session.commit()
            return True

    def DeclineInvite(self, invite_id, user_id):
        try:
            invite = self.session.query(Team).filter(Team.id == invite_id).filter(Team.status == Team.STATUS_PENDING).one()
        except Exception, e:
            log.error('soemthing horrible happened while trying to RSVP to invite id %s' % (str(invite_id)))
            return

        if invite.player_two == user_id:
            invite.status = Team.STATUS_DECLINED
            self.session.add(invite)
            self.session.commit()
            return True
        elif invite.player_one == user_id:
            invite.status = Team.STATUS_CANCELLED
            self.session.add(invite)
            self.session.commit()
            return True

class BaseData():
    """base data, populates base.html template based on current user"""
    menu_items = (('Home', '/'), ('Players', '/players'), ('Teams', '/teams'), ('History', '/history'), ('Readme', '/readme'))

    def __init__(self):
        self.auth = Auth()

    def GetBaseData(self, current_user, current_view):
        data = {}
        data['menu'] = self.menu_items
        if current_user.is_authenticated():
            data['user_profile_url'] = '/players/%s' % (str(current_user.id))
            data['user_name'] = current_user.name
            data['user_id'] = current_user.id
            if self.auth._is_admin(current_user.id):
                data['admin'] = True
        else:
            data['anonymous'] = True
            data['id'] = -1
            data['loginform'] = LoginForm()

        data['current_view'] = current_view

        return data

class Auth():
    def __init__(self):
        self.session = get_db_session()

    def _is_admin(self, user_id):
        try:
            user_id = int(user_id)
        except ValueError, e:
            return

        try:
            admin = self.session.query(Admin).filter_by(player_id=user_id).one()
        except NoResultFound:
            return
        except Exception, e:
            log.error('Exception %s thrown checking admin status of %s!' % (repr(e), str(user_id)))
            return

        if admin is not None:
            return True

    def _make_pw_reset_link(self, user_id, server_name):

        reset_hash = "%s%s" % (md5(os.urandom(8)).hexdigest(), md5(os.urandom(8)).hexdigest())

        pw_reset = None

        try:
            pw_reset = self.session.query(PasswordReset).filter_by(player_id = user_id).one()
        except Exception, e:
            if type(e) != NoResultFound:
                log.error('Unable to generate password reset link for %s due to SQLAlchemy exception %s' % (str(user_id), repr(e)))
                return

        if pw_reset is None:
            pw_reset = PasswordReset(user_id, reset_hash)
        else:
            pw_reset.reset_hash = reset_hash

        self.session.add(pw_reset)
        self.session.commit()

        reset_link = 'http://%s/pw_reset/%s' % (server_name, reset_hash)
        return reset_link

    def ValidateLogin(self, **kwargs):
        password = kwargs['password']
        email = str(kwargs['email']).strip().lower()
        try:
            player = self.session.query(Player).filter_by(email=email).one()
        except NoResultFound:
            return

        if check_hash(password, player.password):
            return True

    def Login(self, player):
        player.authenticated = True
        self.session.add(player)
        self.session.commit()

    def Logout(self, current_player):
        player = self.GetPlayerByEmail(current_player.email)
        player.authenticated = False
        self.session.add(player)
        self.session.commit()

    def ForgotPassword(self, mail_io, user_email, server_name):

        player = self.GetPlayerByEmail(user_email)
        if player is not None:
            reset_link = self._make_pw_reset_link(player.id, server_name)
        else:
            log.debug('player %s not found in player db' % (user_email))
            return
        msg = Message(subject='Foosview password reset', recipients = [user_email],\
            body='Your Foosview password reset link is %s' % (reset_link))

        try:
            mail_io.send(msg)
        except Exception, e:
            log.error('Error sending password reset email to %s' % (player.email))
            return

        return True

    def GetPlayerByResetHash(self, reset_hash):
        pass_reset = None

        try:
            pass_reset = self.session.query(PasswordReset).filter(PasswordReset.reset_hash == reset_hash).one()
        except NoResultFound:
            return

        if pass_reset is not None:
            return self.GetPlayerByID(pass_reset.player_id)

    def InvalidatePasswordResets(self, player_id):
        self.session.query(PasswordReset).filter(PasswordReset.player_id == player_id).delete()
        self.session.commit()

    def GetPlayerByEmail(self, email):
        email = str(email).strip().lower()
        try:
            player = self.session.query(Player).filter_by(email=email).one()
        except NoResultFound:
            return

        return player

    def GetPlayerByID(self, player_id):
        try:
            id = int(player_id)
        except ValueError, e:
            return

        try:
            player = self.session.query(Player).filter_by(id=player_id).one()
        except NoResultFound:
            return
        except Exception, e:
            log.error('Exception thrown trying to get player %s!' % (str(player_id)))
            return

        return player

    @classmethod
    def RequiresAdmin(cls, func):
        """decorator to protect views to admins only"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            db_session = get_db_session()
            if current_user.is_authenticated():
                try:
                    admin = db_session.query(Admin).filter_by(player_id = current_user.id).one()
                except NoResultFound:
                    return redirect(url_for('FoosView:index'))
                except Exception, e:
                    log.error('Exception %s thrown checking admin status of %s!' % (repr(e), str(id)))
                    return redirect(url_for('FoosView:index'))
                if admin is not None:
                    return func(*args, **kwargs)
            return redirect(url_for('FoosView:index'))
        return wrapper
