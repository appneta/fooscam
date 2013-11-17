from flask import Blueprint, request, flash, session, redirect, url_for, g, jsonify
from flask.ext.login import current_user, logout_user, login_user, login_required

from foosweb.controllers.base import BaseData
from foosweb.controllers.player import PlayerData

from foosweb.utils import render_pretty

mod = Blueprint('history', __name__, url_prefix='/history')

import pdb
import logging

log = logging.getLogger(__name__)

@mod.route('/')
def index():
    g.menu_item = 'History'
    data = BaseData.GetBaseData()
    return render_pretty('history_view.html', hist_url='/history/livehistjson', **data)

@mod.route('/livehistjson')
def live_history():
    pd = PlayerData()
    return jsonify(aaData=pd.GetHistory(formatted=True))

@mod.route('/livehistjson/<int:player_id>')
def live_history_id(player_id):
    pd = PlayerData()
    return jsonify(aaData=pd.GetHistory(id=player_id, formatted=True))
