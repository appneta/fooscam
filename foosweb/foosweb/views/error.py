from flask import Blueprint, request, flash, session, redirect, url_for, g, jsonify

from foosweb.controllers.base import BaseData
from foosweb.utils import render_pretty

mod = Blueprint('error', __name__)

import pdb
import logging

log = logging.getLogger(__name__)

@mod.app_errorhandler(404)
def not_found(e):
    data = BaseData.GetBaseData()
    return render_pretty('404.html', **data)
