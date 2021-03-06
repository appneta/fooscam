from flask import Blueprint, request, render_template, flash, session, redirect, url_for

from BeautifulSoup import BeautifulSoup as bs

from flask.ext.login import current_user, logout_user, login_user, login_required

from foosweb.utils import render_pretty
from foosweb.app import db
from foosweb.forms.player import LoginForm, SignupForm, RequestResetForm
from foosweb.models import Player
from foosweb.controllers.base import BaseData
from foosweb.controllers.auth import Auth

mod = Blueprint('auth', __name__)

import pdb

@mod.route('/login', methods = ['POST'])
def login():
    loginform = LoginForm(request.form)
    if loginform.validate():
        if loginform.validate_login():
            player = Player.query.filter_by(email=str(request.form['email'].strip().lower())).one()
            login_user(player)
            Auth.Login(player)
            flash('Welcome back to FoosView %s!' % (player.name), 'alert-success')
            return redirect(request.referrer or url_for('foos.index'))

    flash('Invalid user id or password.', 'alert-danger')
    return redirect(request.referrer or url_for('foos.index'))

@mod.route('/logout')
def logout():
    Auth.Logout(current_user)
    logout_user()
    flash('Logged out', 'alert-info')
    return redirect(url_for('foos.index'))

@mod.route('/pw_reset')
def request_password_reset():
    data = BaseData.GetBaseData()
    request_reset_form = RequestResetForm()
    return render_pretty('request_reset.html', request_reset_form = request_reset_form, **data)

@mod.route('/pw_reset/request', methods=['POST'])
def create_password_reset():
    data = BaseData.GetBaseData()
    request_reset_form = RequestResetForm(request.form)
    if request_reset_form.validate():
        auth = Auth()
        if auth.ForgotPassword(request_reset_form.email.data):
            flash('Password reset sent.', 'alert-success')
        else:
            flash('User not found.', 'alert-danger')
    else:
        return render_pretty('request_reset.html', request_reset_form = request_reset_form, **data)
    return redirect(url_for('foos.index'))

@mod.route('/pw_reset/<string:reset_hash>', methods=['GET'])
def do_password_reset(reset_hash):
    data = BaseData.GetBaseData()
    auth = Auth()
    player = auth.GetPlayerByResetHash(reset_hash)
    if player is not None:
        login_user(player)
        auth.Login(player)
        auth.InvalidatePasswordResets(player.id)
        flash('Hi %s, you should change your password right now!' % (player.name), 'alert-danger')
        return redirect(url_for('players.show_settings'))
    else:
        flash('That reset link has expired', 'alert-warning')
        return redirect(url_for('foos.index'))
