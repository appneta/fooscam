from flask import Flask, redirect, render_template, url_for, abort
from flask.ext.restful import Api
from flask.ext.assets import Environment, Bundle

import logging
import pdb

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

from views import LiveHistory, Score, Players, Status, PlayerHistory
from foosweb import GameWatch, PlayerData

app = Flask(__name__)
api = Api(app)
api.add_resource(Score, '/score', endpoint = 'score')
api.add_resource(Players, '/current_players', endpoint = 'current_players')
api.add_resource(Status, '/status', endpoint = 'status')
api.add_resource(LiveHistory, '/livehistjson', endpoint = 'livehistjson')
api.add_resource(PlayerHistory, '/playerhistjson/<int:id>', endpoint = 'playerhistjson')

assets = Environment(app)
main_js = Bundle('js/modernizr-2.6.2.min.js', 'js/jquery-latest.min.js', 'js/jquery-ui.js')
main_css = Bundle('css/normalize.css', 'css/main.css')
foos_js = Bundle('js/foosview.js')
foos_css = Bundle('css/foosview.css')
hist_js = Bundle('js/jquery.dataTables.min.js', 'js/foos-stats.js')
hist_css = Bundle('css/jquery.dataTables.css')

assets.register('js', main_js)
assets.register('css', main_css)
assets.register('foos_js', foos_js)
assets.register('foos_css', foos_css)
assets.register('hist_js', hist_js)
assets.register('hist_css', hist_css)

menu_items = [{'name': 'Home', 'url': '/'}, \
     {'name': 'History', 'url': '/history'}, \
     {'name': 'Readme', 'url': '/readme'}]

@app.route('/')
def home():
    #return render_template('foosview.html', debug_image='static/img/table.png', menu=all_but('Home'))
    return render_template('foosview.html', menu=all_but('Home'))

#TODO: all players view @app.route('/players/')

@app.route('/players/<int:id>')
def player(id=-1):
    pd = PlayerData()
    profile = pd.GetProfile(id)
    profile['menu'] = menu_items
    return render_template('player_view.html', **profile)

@app.route('/history')
def live_hist():
    return render_template('history.html', hist_url='/livehistjson', menu=all_but('History'))

@app.route('/readme')
def readme():
    return render_template('readme.html', menu=all_but('Readme'))
    #return redirect(url_for('static', filename='readme.html'))

def all_but(entry):
    menu = []
    for item in menu_items:
        if item['name'] != entry:
            menu.append(item)
    return menu

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
