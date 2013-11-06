from flask.ext.restful import Resource, reqparse
from foosweb import GameWatch

from BeautifulSoup import BeautifulSoup as bs

from flask import Flask, redirect, render_template, url_for, abort, request, flash
from flask.ext.classy import FlaskView, route
from flask.ext.login import current_user, logout_user, login_user
from flask import Response
import json

from controllers import PlayerData, RenderData, TeamData, Auth
from forms import LoginForm

import pdb
import logging

log = logging.getLogger(__name__)

def render_pretty(template_name, **kwargs):
    soup = bs(render_template(template_name, **kwargs)).prettify()
    return soup

class FoosView(FlaskView):
    route_base = '/'
    def index(self):
        loginform = LoginForm()
        rd = RenderData()
        loginform = LoginForm(request.form)
        data = rd.Get(current_user, '/')
        return render_pretty('foosview.html', loginform=loginform, debug_image='static/img/table.png', **data)
        #return render_pretty('foosview.html', debug_image='static/img/table.png', **data)

class PlayersView(FlaskView):
    def index(self):
        loginform = LoginForm()
        pd = PlayerData()
        rd = RenderData()
        data = rd.Get(current_user, '/players')
        players = pd.GetAllPlayers()
        return render_pretty('players.html', loginform=loginform, **dict(players.items() + data.items()))

    def get(self, id):
        loginform = LoginForm()
        pd = PlayerData()
        rd = RenderData()
        data = rd.Get(current_user, '/players/%s' % (str(id)))
        profile = pd.GetProfile(id)
        return render_pretty('player_view.html',loginform=loginform, **dict(profile.items() + data.items()))

class TeamsView(FlaskView):
    def index(self):
        loginform = LoginForm()
        pd = PlayerData()
        rd = RenderData()
        td = TeamData()
        data = rd.Get(current_user, '/teams')
        teams = td.TeamList()
        return render_pretty('teamlist.html', loginform=loginform, teams=teams, **data)

    def get(self, id):
        return str(id)

class HistoryView(FlaskView):
    def index(self):
        loginform = LoginForm()
        rd = RenderData()
        data = rd.Get(current_user, '/history')
        return render_pretty('history_view.html', loginform=loginform, hist_url='/livehistjson', **data)

class ReadmeView(FlaskView):
    def index(self):
        loginform = LoginForm()
        rd = RenderData()
        data = rd.Get(current_user, '/readme')
        return render_pretty('readme.html', loginform=loginform, **data)

class AdminView(FlaskView):
    def index(self):
        rd = RenderData()
        data = rd.Get(current_user, '/admin')
        return render_pretty('admin.html', **data)

class AuthView(FlaskView):
    route_base = '/'
    def index(self):
        return redirect(request.referrer or url_for('Foosview:index'))

    @route('/login', methods = ['POST'])
    def login(self):
        rd = RenderData()
        auth = Auth()
        data = rd.Get(current_user, '/login')
        loginform = LoginForm(request.form)
        if loginform.validate():
            if auth.Login(**request.form.to_dict()):
                player=auth.GetPlayerByEmail(loginform.email.data)
                login_user(player)
                flash('Welcome back to FoosView %s!' % (player.name), 'alert-success')
                flash('LOGIN CLASSY', 'alert-success')
        return redirect(request.referrer or url_for('Foosview:index'))

    def logout(self):
        auth = Auth()
        auth.Logout(current_user)
        logout_user()
        flash('Logged out', 'alert-info')
        return redirect(request.referrer or url_for('Foosview:index'))

class TeamupView(FlaskView):
    def get(self, id):
        pass

#Flask-Restful API endpoints
class PlayerHistory(Resource):
    def get(self, id):
        pd = PlayerData()
        return {'aaData': pd.GetHistory(id, formatted=True)}

class LiveHistory(Resource):
    def get(self):
        pd = PlayerData()
        return {'aaData': pd.GetHistory(formatted=True)}

class Status(Resource):
    def get(self):
        gw = GameWatch()
        if gw.GetWinner():
            #game is won, huzzah!
            return {'status': gw.GetWinner()}
        else:
            if gw.IsGameOn():
                return {'status': 'gameon'}
            else:
                return {'status': 'gameoff'}

class Score(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('score', type = dict, required = True, help = 'No score data provided', location = 'json')
        super(Score, self).__init__()

    def get(self):
        gw = GameWatch()
        if not gw.IsGameOn():
            return {'score': {'red' : '', 'blue': ''}}
        else:
            red_score, blue_score = gw.GetScore()
            return {'score': {'red': red_score, 'blue': blue_score}}

    def post(self):
        log.debug('score posted')
        args = self.reqparse.parse_args()
        try:
            red_score = int(args['score']['red'])
            blue_score = int(args['score']['blue'])
        except (KeyError, ValueError):
            return {'status': 'invalid JSON data'}, 400

        gw = GameWatch()
        gw.UpdateScore({'red': red_score, 'blue': blue_score})
        return {'status': 'accepted'}, 201

class Players(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('team', type = list, required = True, help = 'No team data provided', location = 'json')
        super(Players, self).__init__()

    def post(self):
        log.debug('players posted')
        args = self.reqparse.parse_args()
        if len(args['team']) == 2:
            try:
                blue_off = int(args['team'][0]['blue']['offense'])
                blue_def = int(args['team'][0]['blue']['defense'])
                red_off = int(args['team'][1]['red']['offense'])
                red_def = int(args['team'][1]['red']['defense'])
            except (KeyError, IndexError):
                return {'status': 'invalid JSON data'}, 400
            log.debug('ids = [' + str(blue_off) + ', ' + str(blue_def) + ', ' + str(red_off) + ', ' + str(red_def) + ']')
            gw = GameWatch()
            gw.UpdatePlayers({'bo': blue_off, 'bd': blue_def, 'ro': red_off, 'rd': red_def})
            return {'status': 'accepted'}, 201
        else:
            return {'status': 'invalid JSON data (only TWO teams in foosball!)'}, 400

    def get(self):
        gw = GameWatch()
        pd = PlayerData()
        ids = gw.CurrentPlayerIDs()
        names = pd.GetNames(gw.CurrentPlayerIDs())
        gravatars = pd.GetGravatarURLs(gw.CurrentPlayerIDs())
        return  {'bo': {'name': names['bo'], 'id': ids['bo'], 'gravatar': gravatars['bo']},
                 'bd': {'name': names['bd'], 'id': ids['bd'], 'gravatar': gravatars['bd']},
                 'ro': {'name': names['ro'], 'id': ids['ro'], 'gravatar': gravatars['ro']},
                 'rd': {'name': names['rd'], 'id': ids['rd'], 'gravatar': gravatars['rd']}}

