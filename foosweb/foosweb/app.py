from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy


import logging
import pdb

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

foosapp = Flask(__name__)
foosapp.config.from_object('config')

db = SQLAlchemy(foosapp)

#import this after db is initualized above
from foosweb.views.player import mod as playersModule
#app.register_blueprint(playersModule)
