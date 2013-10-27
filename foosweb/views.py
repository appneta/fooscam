from flask import render_template, url_for
from flask.ext.restful import Api, Resource, reqparse
from flask import abort

from foosweb import GameWatch

import logging

log = logging.getLogger('gamewatch')

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
        ids = gw.GetIDs()
        return  {'bo': {'name': names['bo'], 'id': ids['bo']},
                 'bd': {'name': names['bd'], 'id': ids['bd']},
                 'ro': {'name': names['ro'], 'id': ids['ro']},
                 'rd': {'name': names['rd'], 'id': ids['rd']}}

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

