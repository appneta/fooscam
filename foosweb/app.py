from flask import Flask, redirect, render_template, url_for, abort, request, flash
from flask.ext.restful import Api
from flask.ext.assets import Environment, Bundle
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf.csrf import CsrfProtect
from BeautifulSoup import BeautifulSoup as bs

import logging
import pdb

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

from views import LiveHistory, Score, Players, Status, PlayerHistory
from foosweb import GameWatch, PlayerData
from helpers import LoginForm, Auth, RenderData, TeamupForm, TeamData

app = Flask(__name__)
app.secret_key = 'my socrates note'
api = Api(app)
api.add_resource(Score, '/score', endpoint = 'score')
api.add_resource(Players, '/current_players', endpoint = 'current_players')
api.add_resource(Status, '/status', endpoint = 'status')
api.add_resource(LiveHistory, '/livehistjson', endpoint = 'livehistjson')
api.add_resource(PlayerHistory, '/playerhistjson/<int:id>', endpoint = 'playerhistjson')

assets = Environment(app)
main_js = Bundle('js/modernizr-2.6.2.min.js', 'js/jquery-latest.min.js', 'js/jquery-ui.js')
main_css = Bundle('css/normalize.css', 'css/main.css')
players_css = Bundle('css/players.css')
foos_js = Bundle('js/foosview.js')
foos_css = Bundle('css/foosview.css')
hist_js = Bundle('js/jquery.dataTables.min.js', 'js/foos-stats.js')
hist_css = Bundle('css/jquery.dataTables.css')

assets.register('js', main_js)
assets.register('css', main_css)
assets.register('foos_js', foos_js)
assets.register('foos_css', foos_css)
assets.register('hist_js', hist_js)
assets.register('hist_css', hist_css)
assets.register('players_css', players_css)

lm = LoginManager()
lm.init_app(app)

csrf = CsrfProtect()
csrf.init_app(app)

rd = RenderData()
auth = Auth()
pd = PlayerData()
td = TeamData()

@app.route('/')
def home():
    data = rd.Get(current_user)
    return render_template('foosview.html', debug_image='static/img/table.png', **data)
    #return render_template('foosview.html', menu=all_but('Home'))

@app.route('/admin')
def admin():
    if current_user.is_authenticated():
        if auth.IsAdmin(current_user.id):
            data = rd.Get(current_user)
            return render_template('admin.html', **data)
    return redirect(url_for('home'))

@app.route('/teams')
def teamlist():
    data = rd.Get(current_user)
    teams = td.TeamList()
    return render_template('teamlist.html', teams=teams, **data)

@app.route('/teamup/<int:id>', methods=['GET', 'POST'])
@login_required
def teamup(id):
    data = rd.Get(current_user)
    profile_name = pd._get_name_by_id(id)
    form = TeamupForm(request.form)
    if request.method == 'POST' and form.validate():
        if td.SendInvite(from_player=current_user.id, to_player=id, team_name=form.team_name.data):
            flash('Invite to %s sent!' % (profile_name), 'info')
        else:
            flash('Error sending invite!', 'error')
        return redirect(url_for('home'))
    return render_template('teamup.html', form=form, profile_id=id, profile_name=profile_name, **data)

@app.route('/teamup/invites')
@login_required
def show_invites():
    data = rd.Get(current_user)
    invites = td.GetInvitesFor(current_user.id)
    return render_template('teamup_invites.html', invites=invites, **data)

@app.route('/teamup/accept/<int:invite_id>')
@login_required
def teamup_accept(invite_id):
    if td.AcceptInvite(invite_id, current_user.id):
        flash('You dun teamed up!')
    return redirect(url_for('home'))

@app.route('/teamup/decline/<int:invite_id>')
@login_required
def teamup_decline(invite_id):
    if td.DeclineInvite(invite_id, current_user.id):
        flash('Invite cancelled.')
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    data = rd.Get(current_user)
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        if auth.Login(**request.form.to_dict()):
            player=auth.GetPlayerByEmail(form.email.data)
            login_user(player)
            flash('Welcome back to FoosView %s!' % (player.name))
            return redirect(url_for('home'))
    else:
        return render_template('login.html', form=form, **data)

@app.route('/logout')
def logout():
    auth.Logout(current_user)
    logout_user()
    flash('Logged out')
    return redirect(url_for('home'))

@app.route('/players')
def players():
    data = rd.Get(current_user)
    players = pd.GetAllPlayers()
    return render_template('players.html', **dict(players.items() + data.items()))

@app.route('/players/<int:id>')
def player(id):
    data = rd.Get(current_user)
    profile = pd.GetProfile(id)
    return render_template('player_view.html', **dict(profile.items() + data.items()))

@app.route('/history')
def live_hist():
    data = rd.Get(current_user)
    return render_template('history_view.html', hist_url='/livehistjson', **data)

@app.route('/readme')
def readme():
    data = rd.Get(current_user)
    return render_template('readme.html', **data)

@lm.user_loader
def user_loader(id):
    return auth.GetPlayerByID(id)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
