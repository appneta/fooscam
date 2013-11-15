from flask import render_template
from BeautifulSoup import BeautifulSoup as bs

def render_pretty(template_name, **kwargs):
    soup = bs(render_template(template_name, **kwargs)).prettify()
    return soup
