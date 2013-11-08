from flask import Flask
from flask.ext.mail import Mail
from flask.ext.restful import Api
from flask.ext.assets import Environment, Bundle
from flask.ext.login import LoginManager
from flask_wtf.csrf import CsrfProtect

#old ajax views
from views import LiveHistory, Status, PlayerHistory
#new ajax views
from views import AjaxScoreView, AjaxPlayersView
#template rendered views
from views import PlayersView, TeamsView, FoosView, HistoryView, ReadmeView, AdminView, AuthView, TeamupView, PassResetView
from controllers import Auth
import logging
import pdb

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

app = Flask(__name__)
app.secret_key = 'my socrates note'
api = Api(app)

#XXX: convert these read only JSON endpoints from flask-restful to flask-classy?
api.add_resource(Status, '/status', endpoint = 'status')
api.add_resource(LiveHistory, '/livehistjson', endpoint = 'livehistjson')
api.add_resource(PlayerHistory, '/playerhistjson/<int:id>', endpoint = 'playerhistjson')


assets = Environment(app)
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

#TODO: customize login_required decorator behaviour for anon users
lm = LoginManager()
lm.login_view = '/'
lm.init_app(app)
auth = Auth()
#TODO: define this somewhere else
@lm.user_loader
def user_loader(id):
    return auth.GetPlayerByID(id)

csrf = CsrfProtect()
csrf.init_app(app)
#TODO: protect these endpoints from being POSTed by anything but foostools
csrf._exempt_views.add('views.score_post')
csrf._exempt_views.add('views.players_post')

#register view classes
FoosView.register(app)
AuthView.register(app)
PlayersView.register(app)
TeamsView.register(app)
HistoryView.register(app)
ReadmeView.register(app)
AdminView.register(app)
TeamupView.register(app)
PassResetView.register(app)
AjaxScoreView.register(app)
AjaxPlayersView.register(app)

@app.route('/test')
def test():
    auth = Auth()
    if auth.ForgotPassword(mail, 'guest@appneta.com', app.config['SERVER_NAME']):
        return 'cool'
    else:
        return 'weak'

if __name__ == '__main__':
    app.config.from_object('config.Dev')
    mail = Mail(app)
    app.run()
