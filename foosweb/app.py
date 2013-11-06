from flask import Flask
from flask.ext.restful import Api
from flask.ext.assets import Environment, Bundle
from flask.ext.login import LoginManager
from flask_wtf.csrf import CsrfProtect
from views import LiveHistory, Score, Players, Status, PlayerHistory
#template rendered views
from views import PlayersView, TeamsView, FoosView, HistoryView, ReadmeView, AdminView, AuthView, TeamupView
#ajax views
from views import ScoreView
from controllers import Auth
import logging
import pdb

from flask.ext.classy import FlaskView

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

app = Flask(__name__)
app.secret_key = 'my socrates note'
api = Api(app)
#api.add_resource(Score, '/score', endpoint = 'score')
api.add_resource(Players, '/current_players', endpoint = 'current_players')
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

@lm.user_loader
def user_loader(id):
    return auth.GetPlayerByID(id)

csrf = CsrfProtect()
csrf.init_app(app)
#XXX: this is probably really bad!
csrf._exempt_views.add('views.score_post')

FoosView.register(app)
AuthView.register(app)
PlayersView.register(app)
TeamsView.register(app)
HistoryView.register(app)
ReadmeView.register(app)
AdminView.register(app)
TeamupView.register(app)
ScoreView.register(app)

@csrf.exempt
@app.route('/test')
def test():
    pdb.set_trace()

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
