from flask import Blueprint, request, render_template, flash, session, redirect, url_for

from BeautifulSoup import BeautifulSoup as bs

from flask.ext.login import current_user, logout_user, login_user, login_required

from foosweb.app import db
from foosweb.forms.player import LoginForm, SignupForm
from foosweb.models.player import Player
from foosweb.controllers.base import BaseData
from foosweb.controllers.auth import Auth

mod = Blueprint('auth', __name__)

import pdb
import logging

log = logging.getLogger(__name__)

def render_pretty(template_name, **kwargs):
    soup = bs(render_template(template_name, **kwargs)).prettify()
    return soup

@mod.route('/login', methods = ['POST'])
def login():
    loginform = LoginForm(request.form)
    if loginform.validate():
        if loginform.validate_login():
            player = Player.query.filter_by(email=str(request.form['email'].strip().lower())).one()
            login_user(player)
            Auth.Login(player)
            flash('Welcome back to FoosView %s!' % (player.name), 'alert-success')
            return redirect(request.referrer or url_for('FoosView:index'))

    flash('Invalid user id or password.', 'alert-danger')
    return redirect(request.referrer or url_for('FoosView:index'))

@mod.route('/logout')
def logout():
    Auth.Logout(current_user)
    logout_user()
    flash('Logged out', 'alert-info')
    return redirect(request.referrer or url_for('FoosView:index'))

"""class SignupView(FlaskView):
    route_base = '/'

    @route('/signup', methods = ['GET'])
    def show_signup(self):
        pd = PlayerData()
        data = pd.GetSignupData(current_user, '/signup')
        return render_pretty('signup.html', **data)

    #TODO: protect this route from logged in users
    @route('/signup', methods = ['POST'])
    def process_signup(self):
        pd = PlayerData()
        bd = BaseData()
        data = bd.GetBaseData(current_user, '/signup')
        signup_form = SignupForm(request.form)
        if signup_form.validate():
            new_player = pd.AddNewPlayer(request.form)
            flash('Welcome to FoosView %s!' % (new_player.name), 'alert-success')
            return redirect(url_for('FoosView:index'))
        else:
            return render_pretty('signup.html', signup_form=signup_form, **data)"""


"""class PassResetView(FlaskView):
    route_base = '/'

    @route('/pw_reset')
    def request_password_reset(self):
        bd = BaseData()
        data = bd.GetBaseData(current_user, '/pw_reset')
        request_reset_form = RequestResetForm()
        return render_pretty('request_reset.html', request_reset_form = request_reset_form, **data)

    @route('/pw_reset/request', methods=['POST'])
    def create_password_reset(self):
        request_reset_form = RequestResetForm(request.form)
        if request_reset_form.validate():
            auth = Auth()
            mail = current_app.extensions['mail']
            if auth.ForgotPassword(mail, request_reset_form.email.data, current_app.config['SERVER_NAME']):
                flash('Password reset sent.', 'alert-success')
            else:
                flash('User not found.', 'alert-danger')
        return redirect(url_for('FoosView:index'))

    @route('/pw_reset/<string:reset_hash>', methods=['GET'])
    def new_password_form(self, reset_hash):
        bd = BaseData()
        data = bd.GetBaseData(current_user, '/pw_reset')
        auth = Auth()
        pd = PlayerData()
        player = auth.GetPlayerByResetHash(reset_hash)
        if player is not None:
            login_user(player)
            auth.Login(player)
            auth.InvalidatePasswordResets(player.id)
            flash('Hi %s, you should change your password right now!' % (player.name), 'alert-danger')
            return redirect(url_for('SettingsView:show_settings'))
        else:
            flash('That reset link has expired', 'alert-warning')
            return redirect(url_for('FoosView:index'))"""

"""class SettingsView(FlaskView):
    route_base = '/'

    @route('/settings', methods=['GET'])
    @login_required
    def show_settings(self):
        pd = PlayerData()
        data = pd.GetSettingsData(current_user, '/settings')
        return render_pretty('player_settings.html',  **data)

    @route('/settings', methods=['POST'])
    def process_settings(self):
        pd = PlayerData()
        settings_form = SettingsForm(request.form)
        if settings_form.validate():
            if pd.SetSettingsData(settings_form, current_user):
                flash('Settings saved', 'alert-success')
        else:
            flash('Invalid settings', 'alert-danger')
        return redirect(url_for('SettingsView:show_settings'))"""
