from flask import render_template
from flask.ext.restful import Api, Resource, reqparse
from flask import abort

from foosweb import GameWatch, PlayerData

import logging
from datetime import datetime, timedelta

log = logging.getLogger('gamewatch')

#Flask-Restful API endpoints
class PlayerHistory(Resource):
    def get(self, id):
        pd = PlayerData()
        return {'aaData': pd.GetHistory(id, formatted=True)}

class LiveHistory(Resource):
    def get(self):
        pd = PlayerData()
        return {'aaData': pd.GetHistory(formatted=True)}

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
        pd = PlayerData()
        ids = gw.CurrentPlayerIDs()
        names = pd.GetNames(gw.CurrentPlayerIDs())
        gravatars = pd.GetGravatarURLs(gw.CurrentPlayerIDs())
        return  {'bo': {'name': names['bo'], 'id': ids['bo'], 'gravatar': gravatars['bo']},
                 'bd': {'name': names['bd'], 'id': ids['bd'], 'gravatar': gravatars['bd']},
                 'ro': {'name': names['ro'], 'id': ids['ro'], 'gravatar': gravatars['ro']},
                 'rd': {'name': names['rd'], 'id': ids['rd'], 'gravatar': gravatars['rd']}}

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

