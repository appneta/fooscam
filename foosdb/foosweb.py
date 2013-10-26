from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from flask import Flask, jsonify, redirect, render_template, url_for
from flask.ext.restful import Api, Resource, reqparse
from flask.ext.assets import Environment, Bundle
from flask import abort

import json

import os

from time import time
from datetime import datetime, timedelta

import logging

import pdb

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

ORMBase = declarative_base()

#DB ORM models

class Player(ORMBase):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, name):
        self.name = name

class GameState(ORMBase):
    __tablename__ = 'state'
    id = Column(Integer, primary_key=True)
    game_on = Column(Boolean)
    red_off = Column(Integer, ForeignKey(Player.id), nullable=False)
    red_def = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_off = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_def = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_score = Column(Integer)
    red_score = Column(Integer)
    game_started = Column(Integer)
    fuzzy = Column(Boolean)
    game_winner = Column(String)

    def __init__(self):
        self.id = 1
        self.game_on = False
        self.red_off = -1
        self.red_def = -1
        self.blue_off = -1
        self.blue_def = -1
        self.fuzzy = 0
        self.game_started = 0
        self.game_winner = ''

class Game(ORMBase):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    red_off = Column(Integer, ForeignKey(Player.id), nullable=False)
    red_def = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_off = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_def = Column(Integer, ForeignKey(Player.id), nullable=False)
    winner = Column(String)
    blue_score = Column(Integer)
    red_score = Column(Integer)
    started = Column(Integer)
    ended = Column(Integer)

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

#Flask-Restful API endpoints
class LiveHistory(Resource):
    #TODO: accept param to output by player + wins (total / red / blue)
    #http://www.datatables.net/release-datatables/examples/server_side/server_side.html
    def get(self):
        gw = GameWatch()
        history = gw.GetHistory()
        datatable_array = []
        #format json serializable game history data for history page - http://datatables.net/index
        for game in history:
            game_duration = datetime.fromtimestamp(game.ended) - datetime.fromtimestamp(game.started)
            datatable_array.append([gw.GetNameByID(game.red_off), \
                gw.GetNameByID(game.red_def), \
                gw.GetNameByID(game.blue_off), \
                gw.GetNameByID(game.blue_def), \
                game.red_score, game.blue_score, \
                datetime.fromtimestamp(game.started).strftime('%Y-%m-%d %H:%M:%S'), \
                datetime.fromtimestamp(game.ended).strftime('%Y-%m-%d %H:%M:%S'), \
                str(timedelta(seconds=game_duration.seconds)), \
                game.winner])

        return {'aaData': datatable_array}

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

class Score(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('score', type = dict, required = True, help = 'No score data provided', location = 'json')
        super(Score, self).__init__()

    def get(self):
        gw = GameWatch()
        if not gw.IsGameOn():
            return {'score': {'red' : '', 'blue': ''}}
        else:
            red_score, blue_score = gw.GetScore()
            return {'score': {'red': red_score, 'blue': blue_score}}

    def post(self):
        log.debug('score posted')
        args = self.reqparse.parse_args()
        try:
            red_score = int(args['score']['red'])
            blue_score = int(args['score']['blue'])
        except (KeyError, ValueError):
            return {'status': 'invalid JSON data'}, 400

        gw = GameWatch()
        gw.UpdateScore({'red': red_score, 'blue': blue_score})
        return {'status': 'accepted'}, 201

class Players(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('team', type = list, required = True, help = 'No team data provided', location = 'json')
        super(Players, self).__init__()

    def get(self):
        gw = GameWatch()
        names = gw.GetNames()
        return {'team': [{'blue': {'offense': names['bo'], 'defense': names['bd']}},
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

            log.debug('ids = [' + str(blue_off) + ', ' + str(blue_def) + ', ' + str(red_off) + ', ' + str(red_def) + ']')
            gw = GameWatch()
            gw.UpdatePlayers({'bo': blue_off, 'bd': blue_def, 'ro': red_off, 'rd': red_def})
            return {'status': 'accepted'}, 201
        else:
            return {'status': 'invalid JSON data (only TWO teams in foosball!)'}, 400

class GameWatch():
    """
    main fooswatcher game logic lives in here
    """

    def __init__(self):
        db = create_engine('sqlite:///foosball.db')
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()

        if not os.path.exists('./foosball.db'):
            self.InitializeDB(db)

        #persist current game state by maintaining only 1 row in there
        self.game_state = self.session.query(GameState).filter_by(id=1).first()

        #reset fuzziness between games
        if not self.game_state.game_on:
            self.game_state.fuzzy = False
            self.CommitState()

        #if a game winner has been decided clear from the game state after a short time
        if self.game_state.game_winner != '':
            winner_announced_at = self.session.query(Game.ended).order_by(Game.id.desc()).first()
            if len(winner_announced_at) == 1:
                announce_duration = datetime.fromtimestamp(time()) - datetime.fromtimestamp(winner_announced_at[0])
                if announce_duration.seconds > 2:
                    self.game_state.game_winner = ''
                    self.CommitState()

    def InitializeDB(self, db_obj):
        """build default sqlite database"""
        ORMBase.metadata.create_all(db_obj)
        init_state = GameState()
        self.CommitState(init_state)
        anon_player = Player('Anonymous')
        anon_player.id = -1
        self.session.add(anon_player)
        self.session.commit()

    def UpdatePlayers(self, players):
        """
        do something constructive with the incoming player ID's
        """
        new_ids = [players['bo'], players['bd'], players['ro'], players['rd']]
        current_ids = self.GetIDs()

        #same as it ever was
        if new_ids == current_ids:
            if self.game_state.fuzzy:
                log.debug('got 4 players matching ids for game in progress, reverting fuzzy state')
                self.game_state.fuzzy = False
                self.CommitState()
                return

        #if there was a game on, there ain't now
        if new_ids == [-1, -1, -1,-1]:
            if self.game_state.game_on:
                log.debug("got 4 unknown ID's, ending current game")
                self.GameOver()
                return
            else:
                #if there isn't a game on, who cares?
                log.debug("got 4 unknown ID's, no game to end")
                return

        #one or more incoming ID's are unknown (but not all of them)
        if new_ids != current_ids and (-1 in new_ids):
            if self.game_state.game_on:
                #mark current game fuzzy
                self.game_state.fuzzy = True
                self.CommitState()
                log.debug('fuzzy players detected, ignoring player ids')
                for pair in zip(current_ids, new_ids):
                    if pair[0] != pair[1] and pair[1] != -1:
                        #game is fuzzy AND a valid player id has changed!
                        log.debug('fuzzy game with people moving around, assuming game over')
                        self.GameOver()
                        return
            else:
                log.debug('fuzzy players detected but no game is on')
                return
        else:
            #id change detected and all id's are known
            #TODO: this is ugly flow control
            if not self.game_state.game_on:
                log.debug('4 new ids locked and no game going ... starting a new game!')
            else:
                #TODO: something useful here?
                log.debug('4 new ids locked but game is already going, throwing away current game state and starting a new game')

            try:
                bo = self.session.query(Player).filter_by(id=players['bo']).one()
                bd = self.session.query(Player).filter_by(id=players['bd']).one()
                ro = self.session.query(Player).filter_by(id=players['ro']).one()
                rd = self.session.query(Player).filter_by(id=players['rd']).one()
            except (NoResultFound, MultipleResultsFound), e:
                log.error('unknown player ID submitted, NOT logging game!')
                raise

            self.game_state.blue_off = bo.id
            self.game_state.blue_def = bd.id
            self.game_state.red_off = ro.id
            self.game_state.red_def = rd.id
            self.CommitState()
            self.GameOn()

    def UpdateScore(self, score):
        """
        do something useful with the score
        """

        if not self.game_state.game_on:
            log.debug('ignoring score update while no game underway')
            return
        else:
            log.debug('processing score update while game underway')
            log.debug(str(score['red']) + ' ' + str(self.game_state.red_score) + ' ' + str(score['blue']) + ' ' + str( self.game_state.blue_score))
            #end the game when a score goes from >= 8 to 0
            if (score['red'] == 0 and self.game_state.red_score >=8) or (score['blue'] == 0 and self.game_state.blue_score >=8):
                log.debug('score went from red: ' + str(self.game_state.red_score) + ' blue: ' + str(self.game_state.blue_score) + ' to red: ' + \
                    str(score['red']) + ' blue: ' + str(score['blue']))
                log.debug('assuming game is over and using previous scores to determine winner')
                self.GameOver()
                return
            else:
                if self.game_state.fuzzy:
                    log.debug('minor score change detected and game is fuzzy, ignoring until locked')
                    return
                else:
                    log.debug('minor score change detected and game is locked, updating score')
                    self.game_state.red_score = score['red']
                    self.game_state.blue_score = score['blue']
                    self.CommitState()
                    return

    def GetScore(self):
        return self.game_state.red_score,  self.game_state.blue_score

    def IsGameOn(self):
        return self.game_state.game_on

    def GetNames(self):
        #TODO: this could probably be better ...
        player_names = {}
        player_names['bo'] = self.session.query(Player.name).filter_by(id=self.game_state.blue_off).first()
        player_names['bd'] = self.session.query(Player.name).filter_by(id=self.game_state.blue_def).first()
        player_names['ro'] = self.session.query(Player.name).filter_by(id=self.game_state.red_off).first()
        player_names['rd'] = self.session.query(Player.name).filter_by(id=self.game_state.red_def).first()

        try:
            player_names['bo'] = str(player_names['bo'][0]) if self.game_state.blue_off != -1 else 'None'
            player_names['bd'] = str(player_names['bd'][0]) if self.game_state.blue_def != -1 else 'None'
            player_names['ro'] = str(player_names['ro'][0]) if self.game_state.red_off != -1 else 'None'
            player_names['rd'] = str(player_names['rd'][0]) if self.game_state.red_def != -1 else 'None'
        except Exception, e:
            log.error('player ID tag detected but not in foos db!')
            log.debug(e)

        return player_names

    def GetIDs(self):
        return [self.game_state.blue_off, self.game_state.blue_def, self.game_state.red_off, self.game_state.red_def]

    def GetNameByID(self, player_id):
        return str(self.session.query(Player.name).filter_by(id=player_id).first()[0])

    def GetHistory(self):
        game_history = []
        for game in self.session.query(Game).order_by(Game.id):
            game_history.append(game)

        return game_history

    def GetWinner(self):
        if self.game_state.game_winner == '':
            return None
        else:
            return self.game_state.game_winner

    def GameOver(self):
        """
        determine the winner and record that along with the current game state
        """

        #decide who won and compensate for players not actually sliding the 10th cube into place
        if self.game_state.red_score > self.game_state.blue_score:
            winner = 'red'
            self.game_state.red_score = 10
        elif self.game_state.blue_score > self.game_state.red_score:
            winner = 'blue'
            self.game_state.blue_score = 10
        elif self.game_state.blue_score == self.game_state.red_score:
            winner = 'tie'

        #populate and commit a game state object
        foos_log = Game(winner=winner,\
            blue_score=self.game_state.blue_score,\
            red_score=self.game_state.red_score,\
            red_off=self.game_state.red_off,\
            red_def=self.game_state.red_def,\
            blue_off=self.game_state.blue_off,\
            blue_def=self.game_state.blue_def,\
            started=self.game_state.game_started,\
            ended=int(time()))

        self.session.add(foos_log)
        self.session.commit()

        #set a state object to the winner to update web ui with winning team detected
        self.game_state.game_winner = winner

        self.game_state.game_on = False
        self.game_state.blue_off = -1
        self.game_state.blue_def = -1
        self.game_state.red_off = -1
        self.game_state.red_def = -1
        self.CommitState()

    def GameOn(self):
        self.game_state.game_on = True
        self.game_state.fuzzy = False
        self.game_state.red_score = 0
        self.game_state.blue_score = 0
        self.game_state.game_started = int(time())
        self.CommitState()

    def CommitState(self, state=None):
        if state == None:
            self.session.add(self.game_state)
        else:
            self.session.add(state)
        self.session.commit()

app = Flask(__name__)
api = Api(app)
api.add_resource(Score, '/score', endpoint = 'score')
api.add_resource(Players, '/players', endpoint = 'players')
api.add_resource(Status, '/status', endpoint = 'status')
api.add_resource(LiveHistory, '/livehistjson', endpoint = 'livehistjson')

assets = Environment(app)
js = Bundle('js/foosview.js', 'js/modernizr-2.6.2.min.js')
css = Bundle('css/normalize.css', 'css/main.css', 'css/foosview.css')
assets.register('css', css)
assets.register('js', js)

@app.route('/')
def home():
    return render_template('index.html')#, debug_image='static/img/table.png')

@app.route('/history')
def live_hist():
    return redirect(url_for('static', filename='history.html'))

@app.route('/readme')
def readme():
    return redirect(url_for('static', filename='fooscam.html'))

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
    #uncomment to build db from scratch
    #db = create_engine('sqlite:///foosball.db')
    #ORMBase.metadata.create_all(db)
