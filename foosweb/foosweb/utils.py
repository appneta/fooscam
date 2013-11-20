from flask import render_template, redirect, flash, url_for
from foosweb.models import Player
from BeautifulSoup import BeautifulSoup as bs

def render_pretty(template_name, **kwargs):
    soup = bs(render_template(template_name, **kwargs)).prettify()
    return soup

def user_loader(id):
    return Player.query.filter_by(id=id).first()

def unauthorized():
    flash('Please login to access this page', 'alert-danger')
    return redirect(url_for('foos.index'))
