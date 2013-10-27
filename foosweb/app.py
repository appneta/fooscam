from flask import Flask, redirect, render_template, url_for
from flask.ext.restful import Api
from flask.ext.assets import Environment, Bundle

import logging

from views import LiveHistory, Score, Players, Status
from foosweb import GameWatch, PlayerPage

log = logging.getLogger('gamewatch')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

app = Flask(__name__)
api = Api(app)
api.add_resource(Score, '/score', endpoint = 'score')
api.add_resource(Players, '/current_players', endpoint = 'current_players')
api.add_resource(Status, '/status', endpoint = 'status')
api.add_resource(LiveHistory, '/livehistjson', endpoint = 'livehistjson')

assets = Environment(app)
main_js = Bundle('js/modernizr-2.6.2.min.js')
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

@app.route('/')
def home():
    return render_template('foosview.html', debug_image='static/img/table.png')

#@app.route('/players/')
@app.route('/players/<id>')
def player(id=-1):

    gw = GameWatch()
    player_info = {}
    player_info['name'] = gw.GetNameByID(id)
    player_info['gravatar_url'] = gw.GetGravatarURLByID(id)
    player_info['id'] = id

    return render_template('player_view.html', **player_info)

@app.route('/history')
def live_hist():
    #return redirect(url_for('static', filename='history.html'))
    return render_template('history.html')

@app.route('/readme')
def readme():
    return redirect(url_for('static', filename='readme.html'))


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
    #uncomment to build db from scratch
    #db = create_engine('sqlite:///foosball.db')
    #ORMBase.metadata.create_all(db)
