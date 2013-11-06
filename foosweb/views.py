from flask.ext.restful import Resource

from BeautifulSoup import BeautifulSoup as bs

from werkzeug.exceptions import BadRequest

from flask import Response, redirect, render_template, url_for, abort, request, flash
from flask.ext.classy import FlaskView, route
from flask.ext.login import current_user, logout_user, login_user, login_required
from flask import Response

import json

from controllers import PlayerData, RenderData, TeamData, Auth
from foosweb import GameWatch
from forms import LoginForm, TeamupForm

import pdb
import logging

log = logging.getLogger('gamewatch')

def render_pretty(template_name, **kwargs):
    soup = bs(render_template(template_name, **kwargs)).prettify()
    return soup

#TODO: modify redirect to referrer to understand /?next=etc

class FoosView(FlaskView):
    route_base = '/'

    def index(self):
        loginform = LoginForm()
        rd = RenderData()
        data = rd.Get(current_user, '/')
        return render_pretty('foosview.html', loginform=loginform, debug_image='static/img/table.png', **data)
        #return render_pretty('foosview.html', debug_image='static/img/table.png', **data)

class PlayersView(FlaskView):
    route_base = '/'

    @route('/players')
    def index(self):
        loginform = LoginForm()
        pd = PlayerData()
        rd = RenderData()
        data = rd.Get(current_user, '/players')
        players = pd.GetAllPlayers()
        return render_pretty('players.html', loginform=loginform, **dict(players.items() + data.items()))

    @route('/players/<int:id>', methods = ['GET'])
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
        return redirect(request.referrer or url_for('FoosView:index'))

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
                return redirect(request.referrer or url_for('FoosView:index'))

        flash('Invalid user id or password', 'alert-danger')
        return redirect(request.referrer or url_for('FoosView:index'))

    def logout(self):
        auth = Auth()
        auth.Logout(current_user)
        logout_user()
        flash('Logged out', 'alert-info')
        return redirect(request.referrer or url_for('FoosView:index'))

class TeamupView(FlaskView):
    route_base = '/'

    @route('/teamup/<int:id>', methods=['GET'])
    @login_required
    def show_teamup_form(self, id):
        rd = RenderData()
        pd = PlayerData()
        data = rd.Get(current_user, '')
        profile_name = pd.GetNameByID(id)
        form = TeamupForm()
        return render_pretty('teamup.html', form=form, profile_id=id, profile_name=profile_name, **data)

    @route('/teamup/<int:id>', methods=['POST'])
    @login_required
    def process_teamup_form(self, id):
        rd = RenderData()
        pd = PlayerData()
        td = TeamData()
        profile_name = pd.GetNameByID(id)
        form = TeamupForm(request.form)
        pdb.set_trace()
        if form.validate():
            msg = td.ValidateInvite(from_player=current_user.id, to_player=id, team_name=form.team_name.data)
            if msg is None:
                if td.SendInvite(from_player=current_user.id, to_player=id, team_name=form.team_name.data):
                    flash('Invite to %s sent!' % (profile_name), 'alert-success')
                else:
                    flash('Error sending invite!', 'alert-danger')
                return redirect(url_for('FoosView:index'))
            else:
                flash(msg, 'alert-warning')
                return redirect(url_for('FoosView:index'))
        else:
            flash('Error processing form', 'alert-danger')
            return redirect(request.referrer or url_for('FoosView:index'))

    @route('/teamup/invites')
    @login_required
    def invites(self):
        rd = RenderData()
        td = TeamData()
        data = rd.Get(current_user, '/teamup/invites')
        invites = td.GetInvitesFor(current_user.id)
        return render_pretty('teamup_invites.html', invites=invites, **data)

    @route('/teamup/accept/<int:invite_id>')
    @login_required
    def teamup_accept_invite(self, invite_id):
        td = TeamData()
        if td.AcceptInvite(invite_id, current_user.id):
            flash('You dun teamed up!', 'alert-success')
        else:
            flash('Error accepting invite!', 'alert-danger')
        return redirect(request.referrer or url_for('FoosView:index'))

    @route('/teamup/decline/<int:invite_id>')
    @login_required
    def teamup_decline_invite(self, invite_id):
        td = TeamData()
        if td.DeclineInvite(invite_id, current_user.id):
            flash('Invite cancelled.', 'alert-warning')
        return redirect(request.referrer or url_for('FoosView:index'))

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

class AjaxScoreView(FlaskView):
    route_base = '/'

    @route('/score', methods=['GET'])
    def score_get(self):
        gw = GameWatch()
        if not gw.IsGameOn():
            return Response(json.dumps({'score': {'red': '', 'blue': ''}}), content_type='application/json')
        else:
            red_score, blue_score = gw.GetScore()
            return Response(json.dumps({'score': {'red': red_score, 'blue': blue_score}}), content_type='application/json')

    @route('/score', methods=['POST'])
    def score_post(self):
        try:
            json_dict = request.json
        except BadRequest, e:
            log.warn('non-JSON payload posted to score update endpoint!')
            log.debug('Invalid data: %s' % (request.data))
            raise

        try:
            red_score = int(json_dict['score']['red'])
            blue_score = int(json_dict['score']['blue'])
        except (KeyError, ValueError):
            log.warn('Invalid JSON payload posted to score update endpoint!')
            log.debug('Invalid JSON: %s' % (request.json))
            abort(400, 'Invalid JSON Data')

        gw = GameWatch()
        #TODO: this method call doesn't need a dict
        gw.UpdateScore({'red': red_score, 'blue': blue_score})
        return (json.dumps({'status': 'accepted'}), 201, {'Content-Type': 'application/json'})

class AjaxPlayersView(FlaskView):
    route_base='/'

    @route('/current_players', methods = ['GET'])
    def players_get(self):
        gw = GameWatch()
        pd = PlayerData()
        ids = gw.CurrentPlayerIDs()
        names = pd.GetNames(gw.CurrentPlayerIDs())
        gravatars = pd.GetGravatarURLs(gw.CurrentPlayerIDs())
        return  (json.dumps({'bo': {'name': names['bo'], 'id': ids['bo'], 'gravatar': gravatars['bo']},\
                 'bd': {'name': names['bd'], 'id': ids['bd'], 'gravatar': gravatars['bd']},\
                 'ro': {'name': names['ro'], 'id': ids['ro'], 'gravatar': gravatars['ro']},\
                 'rd': {'name': names['rd'], 'id': ids['rd'], 'gravatar': gravatars['rd']}}), 200, {'Content-Type': 'application/json'})

    @route('/current_players', methods = ['POST'])
    def players_post(self):
        try:
            json_dict = request.json
        except BadRequest, e:
            log.warn('non-JSON payload posted to score update endpoint!')
            log.debug('Invalid data: %s' % (request.data))
            raise

        if json_dict.has_key(u'team'):
            if len(json_dict[u'team']) == 2:
                try:
                    blue_off = int(json_dict['team'][0]['blue']['offense'])
                    blue_def = int(json_dict['team'][0]['blue']['defense'])
                    red_off = int(json_dict['team'][1]['red']['offense'])
                    red_def = int(json_dict['team'][1]['red']['defense'])
                except (KeyError, IndexError):
                    abort(400, 'Invalid JSON Data')

            gw = GameWatch()
            gw.UpdatePlayers({'bo': blue_off, 'bd': blue_def, 'ro': red_off, 'rd': red_def})
            return (json.dumps({'status': 'accepted'}), 201, {'Content-Type': 'application/json'})

        abort(400, 'Invalid JSON Data')
