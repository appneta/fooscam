from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.assets import Environment, Bundle
from flask.ext.login import LoginManager

import logging
import pdb

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)

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

#import this after db is initualized above
from foosweb.views.player import mod as playersModule
from foosweb.views.auth import mod as authModule
from foosweb.views.foos import mod as foosModule
from foosweb.models.player import Player

@lm.user_loader
def user_loader(id):
    return Player.query.filter_by(id=id).first()

app.register_blueprint(playersModule)
app.register_blueprint(authModule)
app.register_blueprint(foosModule)
