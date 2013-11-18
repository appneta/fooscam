from flask import Blueprint, request, flash, session, redirect, url_for, g
from flask.ext.login import current_user, logout_user, login_user, login_required

from foosweb.forms.player import LoginForm, SignupForm, SettingsForm
from foosweb.controllers.base import BaseData
from foosweb.controllers.player import PlayerData
from foosweb.controllers.auth import Auth
from foosweb.utils import render_pretty

mod = Blueprint('players', __name__, url_prefix='/players')

import pdb

@mod.route('/')
def index():
    g.menu_item = 'Players'
    pd = PlayerData()
    data = pd.GetAllPlayersData()
    return render_pretty('player_list.html', **data)

@mod.route('/me')
def self_profile():
    pd = PlayerData()
    data = pd.GetProfileData(current_user.id)
    return render_pretty('player_profile.html', **data)

@mod.route('/<int:profile_id>')
def get(profile_id):
    pd = PlayerData()
    data = pd.GetProfileData(profile_id)
    return render_pretty('player_profile.html', **data)

@mod.route('/signup', methods = ['GET'])
def show_signup():
    if not current_user.is_anonymous():
        flash('Y U NEED TWO ACCOUNTS?', 'alert-warning')
        return redirect(url_for('foos.index'))

    data = PlayerData.GetSignupData()
    return render_pretty('signup.html', **data)

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
        return redirect(url_for('players.index'))
    else:
        return render_pretty('signup.html', signup_form=signup_form, **data)

@mod.route('/me/settings', methods=['GET'])
@login_required
def show_settings():
    g.menu_item = 'Settings'
    pd = PlayerData()
    data = pd.GetSettingsData()
    return render_pretty('player_settings.html',  **data)

@mod.route('/me/settings', methods=['POST'])
def process_settings():
    pd = PlayerData()
    settings_form = SettingsForm(request.form)
    if settings_form.validate():
        if pd.SetSettingsData(settings_form, current_user):
            flash('Settings saved', 'alert-success')
    else:
        return render_pretty('player_settings.html', settings_form=settings_form)
    return redirect(url_for('players.show_settings'))
