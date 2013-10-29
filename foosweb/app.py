from flask import Flask, redirect, render_template, url_for, abort, request
from flask.ext.restful import Api
from flask.ext.assets import Environment, Bundle
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required

import logging
import pdb

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

from views import LiveHistory, Score, Players, Status, PlayerHistory
from foosweb import GameWatch, PlayerData
from helpers import LoginForm, Auth, Menu

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

lm = LoginManager()
lm.init_app(app)

@app.route('/')
def home():
    menu = Menu(current_user, 'Home')
    data = menu.Make()
    return render_template('foosview.html', debug_image='static/img/table.png', **data)
    #return render_template('foosview.html', menu=all_but('Home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    menu = Menu(current_user, 'Profile')
    data = menu.Make()
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        auth = Auth()
        player=auth.GetPlayerByEmail(form.email.data)
        login_user(player)
        return redirect(url_for('home'))
    return render_template('login.html', form=form, **data)

@app.route('/logout')
def logout():
    auth = Auth()
    auth.Logout(current_user)
    logout_user()
    return redirect(url_for('home'))

#TODO: all players view @app.route('/players/')

@app.route('/players/<int:id>')
def player(id=-1):
    pd = PlayerData()
    profile = pd.GetProfile(id)
    menu = Menu(current_user, 'Profile')
    data = menu.Make()
    return render_template('player_view.html', **dict(profile.items() + data.items()))

@app.route('/history')
def live_hist():
    menu = Menu(current_user, 'History')
    data = menu.Make()
    return render_template('history_view.html', hist_url='/livehistjson', **data)

@app.route('/readme')
def readme():
    menu = Menu(current_user, 'Readme')
    data = menu.Make()
    return render_template('readme.html', **data)

@lm.user_loader
def user_loader(id):
    auth = Auth()
    return auth.GetPlayerByID(id)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
