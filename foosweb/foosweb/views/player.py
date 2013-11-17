from flask import Blueprint, request, flash, session, redirect, url_for, g
from flask.ext.login import current_user, logout_user, login_user, login_required

from foosweb.forms.player import LoginForm, SignupForm
from foosweb.controllers.base import BaseData
from foosweb.controllers.player import PlayerData
from foosweb.controllers.auth import Auth
from foosweb.utils import render_pretty

mod = Blueprint('players', __name__, url_prefix='/players')

import pdb
import logging

log = logging.getLogger(__name__)

@mod.route('/')
def index():
    g.menu_item = '/players'
    #data = BaseData.GetBaseData()
    pd = PlayerData()
    data = pd.GetAllPlayersData()
    return render_pretty('players.html', **data)

@mod.route('/me')
def self_profile():
    return render_pretty('profile.html')

@mod.route('/<int:profile_id>')
def get(profile_id):
    pd = PlayerData()
    data = pd.GetProfileData(profile_id)
    return render_pretty('player_view.html', **data)

@mod.route('/signup', methods = ['GET'])
def show_signup():
    data = PlayerData.GetSignupData()#current_user, '/signup')
    return render_pretty('signup.html', **data)

#TODO: protect this route from logged in users
@mod.route('/signup', methods = ['POST'])
def process_signup():
    data = BaseData.GetBaseData()
    signup_form = SignupForm(request.form)
    if signup_form.validate():
        pd = PlayerData()
        new_player = pd.AddNewPlayer(request.form)
        login_user(new_player)
        Auth.Login(new_player)
        flash('Welcome to FoosView %s!' % (new_player.name), 'alert-success')
        #return redirect(url_for('FoosView:index'))
        return redirect(url_for('players.index'))
    else:
        return render_pretty('signup.html', signup_form=signup_form, **data)

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
