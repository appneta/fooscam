from flask import Flask, redirect, render_template, url_for, abort, request, flash
from flask.ext.restful import Api
from flask.ext.assets import Environment, Bundle
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf.csrf import CsrfProtect
from BeautifulSoup import BeautifulSoup as bs
from views import LiveHistory, Score, Players, Status, PlayerHistory
from forms import LoginForm, TeamupForm
from controllers import PlayerData, TeamData, RenderData, Auth
import logging
import pdb

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

app = Flask(__name__)
app.secret_key = 'my socrates note'
api = Api(app)
api.add_resource(Score, '/score', endpoint = 'score')
api.add_resource(Players, '/current_players', endpoint = 'current_players')
api.add_resource(Status, '/status', endpoint = 'status')
api.add_resource(LiveHistory, '/livehistjson', endpoint = 'livehistjson')
api.add_resource(PlayerHistory, '/playerhistjson/<int:id>', endpoint = 'playerhistjson')

assets = Environment(app)
#main_js = Bundle('js/modernizr-2.6.2.min.js', 'js/jquery-latest.min.js', 'js/jquery-ui.js')
#main_css = Bundle('css/normalize.css', 'css/main.css')
main_js = Bundle('js/jquery-latest.min.js', 'js/jquery-ui.js', 'js/bootstrap.min.js')
main_css = Bundle('css/bootstrap.min.css', 'css/base.css')
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
lm.login_view = '/login'
lm.init_app(app)

csrf = CsrfProtect()
csrf.init_app(app)

rd = RenderData()
auth = Auth()
pd = PlayerData()
td = TeamData()

@app.route('/')
def home():
    data = rd.Get(current_user, '/')
    return render_template('foosview.html', debug_image='static/img/table.png', **data)
    #return render_template('foosview.html', menu=all_but('Home'))

@app.route('/admin')
@auth.RequiresAdmin
def admin():
    data = rd.Get(current_user, '/admin')
    return render_template('admin.html', **data)

@app.route('/teams')
def teamlist():
    data = rd.Get(current_user, '/teams')
    teams = td.TeamList()
    return render_template('teamlist.html', teams=teams, **data)

@app.route('/teamup/<int:id>', methods=['GET', 'POST'])
@login_required
def teamup(id):
    data = rd.Get(current_user, '')
    profile_name = pd.GetNameByID(id)
    form = TeamupForm(request.form)
    if request.method == 'POST' and form.validate():
        msg = td.ValidateInvite(from_player=current_user.id, to_player=id, team_name=form.team_name.data)
        if msg is None:
            if td.SendInvite(from_player=current_user.id, to_player=id, team_name=form.team_name.data):
                flash('Invite to %s sent!' % (profile_name), 'alert-success')
            else:
                flash('Error sending invite!', 'alert-danger')
            return redirect(url_for('home'))
        else:
            flash(msg, 'alert-warning')
            return redirect(url_for('home'))
    return render_template('teamup.html', form=form, profile_id=id, profile_name=profile_name, **data)

@app.route('/teamup/invites')
@login_required
def show_invites():
    data = rd.Get(current_user, '/teamup/invites')
    invites = td.GetInvitesFor(current_user.id)
    return render_template('teamup_invites.html', invites=invites, **data)

@app.route('/teamup/accept/<int:invite_id>')
@login_required
def teamup_accept(invite_id):
    if td.AcceptInvite(invite_id, current_user.id):
        flash('You dun teamed up!', 'alert-success')
    return redirect(request.referrer)

@app.route('/teamup/decline/<int:invite_id>')
@login_required
def teamup_decline(invite_id):
    if td.DeclineInvite(invite_id, current_user.id):
        flash('Invite cancelled.', 'alert-warning')
    return redirect(request.referrer)

@app.route('/login', methods=['GET', 'POST'])
def login():
    data = rd.Get(current_user, '/login')
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        if auth.Login(**request.form.to_dict()):
            player=auth.GetPlayerByEmail(form.email.data)
            login_user(player)
            flash('Welcome back to FoosView %s!' % (player.name), 'alert-success')
            #TODO: figure out a better way to redirect post login
            return redirect(request.args.get("next") or url_for('home'))
    else:
        return render_template('login.html', form=form, **data)

@app.route('/logout')
def logout():
    auth.Logout(current_user)
    logout_user()
    flash('Logged out', 'alert-info')
    return redirect(url_for('home'))

@app.route('/players')
def players():
    data = rd.Get(current_user, '/players')
    players = pd.GetAllPlayers()
    return render_template('players.html', **dict(players.items() + data.items()))

@app.route('/players/<int:id>')
def player(id):
    data = rd.Get(current_user, '/players/%s' % (str(id)))
    profile = pd.GetProfile(id)
    return render_template('player_view.html', **dict(profile.items() + data.items()))

@app.route('/history')
def live_hist():
    data = rd.Get(current_user, '/history')
    return render_template('history_view.html', hist_url='/livehistjson', **data)

@app.route('/readme')
def readme():
    data = rd.Get(current_user, '/readme')
    return render_template('readme.html', **data)

@lm.user_loader
def user_loader(id):
    return auth.GetPlayerByID(id)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
