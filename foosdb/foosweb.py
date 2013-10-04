from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from flask import Flask, jsonify, redirect, url_for
from flask.ext.restful import Api, Resource, reqparse
from flask import abort

import json

from time import time
from datetime import datetime

import logging

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

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
    game_started = Column(Integer)

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
    started = Column(Integer)
    ended = Column(Integer)

    def __init__(self, winner, blue_score, red_score, red_off, red_def, blue_off, blue_def, started, ended):
        self.red_off = red_off
        self.red_def = red_def
        self.blue_off = blue_off
        self.blue_def = blue_def
        self.winner = winner
        self.blue_score = blue_score
        self.red_score = red_score
        self.started = started
        self.ended = ended

    def __repr__(self):
        gw = GameWatch()
        rep = 'Game ID: ' + str(self.id)
        rep += ' Red Team: (offense) ' + gw.GetNameByID(self.red_off)
        rep += ' (defense) ' + gw.GetNameByID(self.red_def)
        rep += ' Score: ' + str(self.red_score)
        rep += ' Blue Team: (offense) ' + gw.GetNameByID(self.blue_off)
        rep += ' (defense) ' + gw.GetNameByID(self.blue_def)
        rep += ' Score: ' + str(self.blue_score)
        rep += ' Game On: ' + datetime.fromtimestamp(self.started).strftime('%Y-%m-%d %H:%M:%S')
        rep += ' Game Over: ' + datetime.fromtimestamp(self.ended).strftime('%Y-%m-%d %H:%M:%S')
        rep += ' Result: ' + self.winner + ' WINS!'
        return rep

    def Summary(self):
        gw = GameWatch()
        rep = 'Game ID: ' + str(self.id)
        rep += ' Red Team: (offense) ' + gw.GetNameByID(self.red_off)
        rep += ' (defense) ' + gw.GetNameByID(self.red_def)
        rep += ' Score: ' + str(self.red_score)
        rep += ' Blue Team: (offense) ' + gw.GetNameByID(self.blue_off)
        rep += ' (defense) ' + gw.GetNameByID(self.blue_def)
        rep += ' Score: ' + str(self.blue_score)
        rep += ' Game On: ' + datetime.fromtimestamp(self.started).strftime('%Y-%m-%d %H:%M:%S')
        rep += ' Game Over: ' + datetime.fromtimestamp(self.ended).strftime('%Y-%m-%d %H:%M:%S')
        rep += ' Result: ' + self.winner + ' WINS!'
        return rep


class Status(Resource):
    def get(self):
        gw = GameWatch()
        if gw.GetStatus():
            return {'status': 'Game On!'}
        else:
            return {'status': 'Table Open!'}

class Score(Resource):
    """
    flask-restful score handler
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('score', type = dict, required = True, help = 'No score data provided', location = 'json')
        super(Score, self).__init__()

    def get(self):
        gw = GameWatch()
        red_score, blue_score = gw.GetScore()
        return {'score': {'red': red_score, 'blue': blue_score}}

    def post(self):
        args = self.reqparse.parse_args()
        try:
            red_score = args['score']['red']
            blue_score = args['score']['blue']
        except KeyError:
            return {'status': 'invalid JSON data'}, 400

        gw = GameWatch()
        gw.UpdateScore({'red': red_score, 'blue': blue_score})
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
        gw = GameWatch()
        names = gw.GetNames()
        return {'team': [{'blue': {'offense': str(names['bo']), 'defense': names['bd']}},
            {'red': {'offense': names['ro'], 'defense': names['rd']}}]}

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

            log.debug(str(blue_off) + ' ' + str(blue_def) + ' ' + str(red_off) + ' ' + str(red_def))
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
        #persist current game state by maintaining only 1 row in there
        self.game_state = self.session.query(GameState).filter_by(id=1).first()


    def UpdatePlayers(self, players):
        """
        do something constructive with the incoming player ID's
        """
        new_ids = [players['bo'], players['bd'], players['ro'], players['rd']]
        current_ids = self.GetIDs()

        #update game state, try to be clever about it
        if new_ids == [-1, -1, -1,-1]:
            if self.game_state.game_on:
                #if there was a game on, there ain't now
                log.debug("4 unknown ID's incoming, ending current game")
                if self.game_state.game_on:
                    self.GameOver()
                    return
            else:
                log.debug("4 unknown ID's incoming, no game to end")
                return

        if new_ids != current_ids and (-1 in new_ids):
            if self.game_state.game_on:
                #id change detect and at least one id is unknown
                for pair in zip(current_ids, new_ids):
                    if pair[0] != pair[1]:
                        log.debug('fuzzy detection started')
                        #if an ID has changed but < 4 new ID's are unknown don't assume game is over
                        if pair[1] == -1:
                            log.debug('fuzzy players detected, ignoring')
                            #fuzzy
                            return
                        else:
                            #TODO: Allow offense and defense to swap mid game?
                            #if an ID has changed and is now a new valid ID -> game is over
                            log.debug('somebody moved REALLY fast')
                            self.game_state.blue_off = players['bo']
                            self.game_state.blue_def = players['bd']
                            self.game_state.red_off = players['ro']
                            self.game_state.red_def = players['rd']
                            self.CommitState()
                            self.GameOver()
                            return
                    else:
                        #no player change detected in this pair, game continues
                        return
            else:
                log.debug('fuzzy players detected but game is off')
                return
        else:
            #id change detected and all id's are known
            if not self.game_state.game_on:
                log.debug('4 new ids locked and no game going ... starting a new game!')
                self.game_state.blue_off = players['bo']
                self.game_state.blue_def = players['bd']
                self.game_state.red_off = players['ro']
                self.game_state.red_def = players['rd']
                self.CommitState()
                self.GameOn()
            else:
                log.debug('4 ids locked but game is already going')

    def UpdateScore(self, score):
        """
        do something useful with the score
        """
        self.game_state.red_score = score['red']
        self.game_state.blue_score = score['blue']
        self.CommitState()

    def UpdateStatus(self, status):
        """
        game on? game over?
        """
        if status:
            self.game_state.game_on = True
        else:
            self.game_state.game_on = False

        self.CommitState()

    def GetScore(self):
        return self.game_state.red_score,  self.game_state.blue_score

    def GetNames(self):
        player_names = {}
        player_names['bo'] = self.session.query(Player.name).filter_by(id=self.game_state.blue_off).first()
        player_names['bd'] = self.session.query(Player.name).filter_by(id=self.game_state.blue_def).first()
        player_names['ro'] = self.session.query(Player.name).filter_by(id=self.game_state.red_off).first()
        player_names['rd'] = self.session.query(Player.name).filter_by(id=self.game_state.red_def).first()

        try:
            player_names['bo'] = str(player_names['bo'][0])
            player_names['bd'] = str(player_names['bd'][0])
            player_names['ro'] = str(player_names['ro'][0])
            player_names['rd'] = str(player_names['rd'][0])
        except Exception, e:
            log.debug('oh shit')
            log.debug(e)

        return player_names

    def GetIDs(self):
        return [self.game_state.blue_off, self.game_state.blue_def, self.game_state.red_off, self.game_state.red_def]

    def GetNameByID(self, player_id):
        return str(self.session.query(Player.name).filter_by(id=player_id).first()[0])

    def GetStatus(self):
        return self.game_state.game_on

    def GetHistory(self):
        history = []
        for thing in self.session.query(Game).order_by(Game.id):
            history.append(thing)

        return history

    def GameOver(self):
        if self.game_state.red_score > self.game_state.blue_score:
            winner = 'red'
        elif self.game_state.blue_score > self.game_state.red_score:
            winner = 'blue'
        elif self.game_state.blue_score == self.game_state.red_score:
            winner = 'tie'

        #log the game details
        foos_log = Game(winner, self.game_state.blue_score, self.game_state.red_score, \
            self.game_state.red_off, self.game_state.red_def, \
            self.game_state.blue_off, self.game_state.blue_def, \
            self.game_state.game_started, int(time()))

        self.session.add(foos_log)
        self.session.commit()

        self.game_state.game_on = False
        self.game_state.blue_off = -1
        self.game_state.blue_def = -1
        self.game_state.red_off = -1
        self.game_state.red_def = -1
        self.CommitState()

    def GameOn(self):
        self.game_state.game_on = True
        self.game_state.game_started = int(time())
        self.CommitState()

    def CommitState(self):
        self.session.add(self.game_state)
        self.session.commit()

app = Flask(__name__)
api = Api(app)
api.add_resource(Score, '/score', endpoint = 'score')
api.add_resource(Players, '/players', endpoint = 'players')
api.add_resource(Status, '/status', endpoint = 'status')

@app.route('/')
def home():
    return redirect(url_for('static', filename='index.html'))

@app.route('/history')
def games_history():
    gw = GameWatch()
    history = gw.GetHistory()
    output = 'Warning, stats tracking is pretty twitchy. Please report weird and wonky results in #fooscam :)<br><br><br>'
    for line in history:
        output += line.Summary() + '<br>'

    return output


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
