from flask import Blueprint, request, flash, session, redirect, url_for, g, jsonify, current_app
from flask.ext.login import current_user, logout_user, login_user, login_required
from foosweb.utils import render_pretty
from foosweb.gamewatch import GameWatch
from foosweb.controllers.base import BaseData
from foosweb.controllers.player import PlayerData

mod = Blueprint('foos', __name__)

import json
import pdb

@mod.route('/')
def index():
    g.menu_item = 'Home'
    data = BaseData.GetBaseData()
    return render_pretty('foosview.html', debug_image='static/img/table.png', **data)

@mod.route('/status')
def get_status():
    gw = GameWatch()
    if gw.GetWinner():
        return jsonify(status = gw.GetWinner())
    else:
        if gw.IsGameOn():
            return jsonify(status = 'gameon')
        else:
            return jsonify(status = 'gameoff')

@mod.route('/score', methods=['GET'])
def get_score():
    gw = GameWatch()
    if not gw.IsGameOn():
        return jsonify(score = {'red': '', 'blue': ''})
    else:
        red_score, blue_score = gw.GetScore()
        return jsonify(score = {'red': red_score, 'blue': blue_score})

@mod.route('/score', methods=['POST'])
def score_post():
    if request.json is not None:
        json_dict = request.json
    else:
        current_app.logger.warn('non-JSON payload posted to score update endpoint!')
        current_app.logger.debug('Invalid data: %s' % (request.data))
        return jsonify(error = 'data must be posted in json format'), 400

    try:
        red_score = int(json_dict['score']['red'])
        blue_score = int(json_dict['score']['blue'])
    except (KeyError, ValueError):
        current_app.logger.warn('Invalid JSON payload posted to score update endpoint!')
        current_app.logger.debug('Invalid JSON: %s' % (request.json))
        return jsonify(error = 'invalid score json data'), 400

    gw = GameWatch()
    gw.UpdateScore(red_score, blue_score)
    return jsonify(status = 'accepted'), 201

@mod.route('/current_players', methods = ['GET'])
def players_get():
    gw = GameWatch()
    pd = PlayerData()
    ids = gw.CurrentPlayerIDs()
    names = pd.GetCurrentPlayerNames()
    gravatars = pd.GetCurrentPlayerGravatarURLs()
    return  json.dumps({'bo': {'name': names['bo'], 'id': ids['bo'], 'gravatar': gravatars['bo']},\
        'bd': {'name': names['bd'], 'id': ids['bd'], 'gravatar': gravatars['bd']},\
        'ro': {'name': names['ro'], 'id': ids['ro'], 'gravatar': gravatars['ro']},\
        'rd': {'name': names['rd'], 'id': ids['rd'], 'gravatar': gravatars['rd']}}), 200, {'Content-Type': 'application/json'}

@mod.route('/current_players', methods = ['POST'])
def players_post():
    if request.json is not None:
        json_dict = request.json
    else:
        current_app.logger.warn('non-JSON payload posted to score update endpoint!')
        current_app.logger.debug('Invalid data: %s' % (request.data))
        return jsonify(error = 'data must be posted in json format'), 400

    if json_dict.has_key(u'team'):
        if len(json_dict[u'team']) == 2:
            try:
                blue_off = int(json_dict['team'][0]['blue']['offense'])
                blue_def = int(json_dict['team'][0]['blue']['defense'])
                red_off = int(json_dict['team'][1]['red']['offense'])
                red_def = int(json_dict['team'][1]['red']['defense'])
            except (KeyError, IndexError):
                return jsonify(error = 'invalid team data in json'), 400
        else:
            return jsonify(error = 'two and ONLY two teams in foosball'), 400

        gw = GameWatch()
        gw.UpdatePlayers({'bo': blue_off, 'bd': blue_def, 'ro': red_off, 'rd': red_def})
        return jsonify(status = 'accepted'), 201
    return jsonify(error = 'no team key in json'), 400
