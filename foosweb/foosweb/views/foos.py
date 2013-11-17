from flask import Blueprint, request, flash, session, redirect, url_for, g
from flask.ext.login import current_user, logout_user, login_user, login_required
from foosweb.utils import render_pretty

from foosweb.controllers.base import BaseData

mod = Blueprint('foos', __name__)

import pdb
import logging

log = logging.getLogger(__name__)

@mod.route('/')
def index():
    g.menu_item = 'Home'
    data = BaseData.GetBaseData()
    return render_pretty('foosview.html', debug_image='static/img/table.png', **data)
