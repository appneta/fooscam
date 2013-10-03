from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from flask import Flask, jsonify
from flask.ext.restful import Api, Resource, reqparse
from flask import abort

import json

import pdb


ORMBase = declarative_base()

class GameState(ORMBase):
    """
    persistent game state
    """
    __tablename__ = 'state'
    id = Column(Integer, primary_key=True)
    game_on = Column(Boolean)
    red_off = Column(Integer)
    red_def = Column(Integer)
    blue_off = Column(Integer)
    blue_def = Column(Integer)
    blue_score = Column(Integer)
    red_score = Column(Integer)

    def __init__(self):
        self.id = 1
        self.game_on = False

class Player(ORMBase):
    """
    player database class
    """
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, name):
        self.name = name

    """def __repr__(self):
        return "<Player('%s', '%s)" % (self.id, self.name)"""

class Game(ORMBase):
    """
    game database class
    """
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    red_off = Column(Integer)
    red_def = Column(Integer)
    blue_off = Column(Integer)
    blue_def = Column(Integer)
    winner = Column(String)
    blue_score = Column(Integer)
    red_score = Column(Integer)

    def __init__(self, winner, blue_score, red_score, red_off=1, red_def=1, blue_off=1, blue_def=1):
        self.red_off = red_off
        self.red_def = red_def
        self.blue_off = blue_off
        self.blue_def = blue_def
        self.winner = winner
        self.blue_score = blue_score
        self.red_score = red_score

app = Flask(__name__)
api = Api(app)

class Score(Resource):
    """
    flask-restful score handler
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('score', type = dict, required = True, help = 'No score data provided', location = 'json')
        super(Score, self).__init__()

    def get(self):
        pass

    def post(self):
        args = self.reqparse.parse_args()
        try:
            red_score = args['score']['red']
            blue_score = args['score']['blue']
        except KeyError:
            return {'status': 'invalid JSON data'}, 400

        return {'status': 'accepted'}, 201

class Players(Resource):
    """
    flask-restful player handler
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('team', type = list, required = True, help = 'No team data provided', location = 'json')
        super(Players, self).__init__()

    def get(self):
        pass

    def post(self):
        args = self.reqparse.parse_args()
        if len(args['team']) == 2:
            try:
                blue_off = args['team'][0]['blue']['offense']
                blue_def = args['team'][0]['blue']['defense']
                red_off = args['team'][1]['red']['offense']
                red_def = args['team'][1]['red']['defense']
            except (KeyError, IndexError):
                return {'status': 'invalid JSON data'}, 400

            #TODO:
            gw = GameWatch()
            gw.UpdatePlayers({'bo': blue_off, 'bd': blue_def, 'ro': red_off, 'rd': red_def})
            return {'status': 'accepted'}, 201
        else:
            return {'status': 'invalid JSON data (only TWO teams in foosball!)'}, 400

class GameWatch():
    def __init__(self):
        db = create_engine('sqlite:///foosball.db')
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()
        #self.game_state = GameState()
        self.game_state = self.session.query(GameState).filter_by(id=1).first()

    def UpdatePlayers(self, players):
        """
        do something constructive with the state json we receive
        """
        self.game_state.blue_off = players['bo']
        self.game_state.blue_def = players['bd']
        self.game_state.red_off = players['ro']
        self.game_state.red_off = players['rd']

        self.session.add(self.game_state)
        self.session.commit()

    def GetFriendlyJSON(self, ids):
        for id in ids:
            pass

api.add_resource(Score, '/score', endpoint = 'score')
api.add_resource(Players, '/players', endpoint = 'players')

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
