from flask import Blueprint, request, flash, session, redirect, url_for, g, jsonify

from foosweb.controllers.base import BaseData
from foosweb.utils import render_pretty

mod = Blueprint('readme', __name__)

import pdb

@mod.route('/readme')
def show_readme():
    g.menu_item = 'Readme'
    data = BaseData.GetBaseData()
    return render_pretty('readme.html', **data)
