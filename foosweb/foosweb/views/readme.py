from flask import Blueprint, request, flash, session, redirect, url_for, g, jsonify
from flask.ext.login import current_user

from foosweb.controllers.base import BaseData
from foosweb.utils import render_pretty

mod = Blueprint('readme', __name__)

import pdb
import logging

log = logging.getLogger(__name__)

@mod.route('/readme')
def show_readme():
    g.menu_item = 'Readme'
    data = BaseData.GetBaseData()
    return render_pretty('readme.html', **data)
