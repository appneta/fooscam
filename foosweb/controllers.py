from flask import redirect, url_for
from flask.ext.login import current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from datetime import datetime, timedelta
from hashlib import md5
from functools import wraps
from models import Player, Team, Game

import logging
log = logging.getLogger('gamewatch')

#TODO: game state controller

class PlayerData():
    def __init__(self):
        db = create_engine('sqlite:///foosball.db')
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()

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

    def GetAllPlayers(self):
        players = {}
        players['all_players'] = []
        all_players = self.session.query(Player).all()
        #all_players = self.session.query(Player).filter(Player.id<6).all()

        for player in all_players:
            if player.id != -1 and player.name != 'Guest':
                players['all_players'].append((player.id, player.name,  self._get_gravatar_url_by_id(player.id, size=200)))

        return players

    #def GetProfile(self, id, user_id):
    def GetProfile(self, id):
        """Get profile data for id and show it to user_id"""
        profile = {}
        try:
            profile['ro_wins'] = self.session.query(Game).filter(Game.red_off == id).filter(Game.winner == 'red').count()
            profile['rd_wins'] = self.session.query(Game).filter(Game.red_def == id).filter(Game.winner == 'red').count()
            profile['bo_wins'] = self.session.query(Game).filter(Game.blue_off == id).filter(Game.winner == 'blue').count()
            profile['bd_wins'] = self.session.query(Game).filter(Game.blue_def == id).filter(Game.winner == 'blue').count()
        except Exception, e:
            log.error('Failed to get wins from db for id %s with error %s' % (str(id), repr(e)))
            return

        profile['profile_name'] = self.GetNameByID(id)
        profile['profile_id'] = id
        profile['gravatar_url'] = self._get_gravatar_url_by_id(id)
        profile['hist_url'] = '/playerhistjson/' + str(id)
        profile['total_games'] = self.GetHistory(id=id, count=True)
        profile['teams'] = self._get_teams_by_player_id(id)

        return profile

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
        db = create_engine('sqlite:///foosball.db')
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()

        self.pd = PlayerData()

    def TeamList(self):
        teams = self.session.query(Team).all()

        #TODO: add standings data & gravatar for teams
        retvals = []
        for team in teams:
            p_one_name = self.pd.GetNameByID(team.player_one)
            p_two_name = self.pd.GetNameByID(team.player_two)
            retvals.append((team.player_one, p_one_name, team.player_two, p_two_name, team.id, team.name))

        return retvals

    def ValidateInvite(self, from_player=-1, to_player=-1, team_name=''):
        """return None if invite checks out, returns error message if not"""
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
        #TODO: global db session? wrap commit() for table locks
        self.session.commit()
        return True

    def GetInvitesFor(self, id):
        try:
            invites = self.session.query(Team).filter(Team.status == Team.STATUS_PENDING).\
                filter((Team.player_one == id) | (Team.player_two == id)).all()
        except Exception, e:
            log.error('something horrible happened whily trying to find invites for id %s' % (str(id)))
            return

        retvals = []
        for invite in invites:
            p_one_name = self.pd.GetNameByID(invite.player_one)
            p_two_name = self.pd.GetNameByID(invite.player_two)
            retvals.append((invite.player_one, p_one_name, invite.player_two, p_two_name, invite.name, invite.id))

        return retvals

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

class RenderData():
    """base data to customize views for current user"""
    menu_items = (('Home', '/'), ('Players', '/players'), ('Teams', '/teams'), ('History', '/history'), ('Readme', '/readme'))

    def __init__(self):
        self.auth = Auth()

    def Get(self, user, current_view):
        data = {}
        data['menu'] = self.menu_items
        if user.is_authenticated():
            data['user_profile_url'] = '/players/%s' % (str(user.id))
            data['user_name'] = user.name
            data['user_id'] = user.id
            if self.auth._is_admin(user.id):
                data['admin'] = True
        else:
            data['anonymous'] = True
            data['id'] = -1

        data['current_view'] = current_view

        return data

class Auth():
    def __init__(self):
        db = create_engine('sqlite:///foosball.db')
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()

    def _is_admin(self, id):
        try:
            id = int(id)
        except ValueError, e:
            return

        try:
            admin = self.session.query(Admin).filter_by(player_id=id).one()
        except NoResultFound:
            return
        except Exception, e:
            log.error('Exception %s thrown checking admin status of %s!' % (repr(e), str(id)))
            return

        return True

    def Login(self, **kwargs):
        password = md5(kwargs['password']).hexdigest()
        email = str(kwargs['email']).strip().lower()
        try:
            player = self.session.query(Player).filter_by(email=email).filter_by(password=password).one()
        except NoResultFound:
            return

        player.authenticated = True
        self.session.add(player)
        self.session.commit()
        return True

    def Logout(self, current_player):
        player = self.GetPlayerByEmail(current_player.email)
        player.authenticated = False
        self.session.add(player)
        self.session.commit()

    def GetPlayerByEmail(self, email):
        email = str(email).strip().lower()
        try:
            player = self.session.query(Player).filter_by(email=email).one()
        except NoResultFound:
            return
        return player

    def GetPlayerByID(self, id):
        try:
            id = int(id)
        except ValueError, e:
            return

        try:
            player = self.session.query(Player).filter_by(id=id).one()
        except NoResultFound:
            return
        except Exception, e:
            log.error('Exception thrown trying to get player %s!' % (str(id)))
            return

        return player

    def RequiresAdmin(self, func):
        """decorator to protect views to admins only"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated():
                if self._is_admin(current_user.id):
                    return func(*args, **kwargs)
            return redirect(url_for('home'))
        return wrapper
