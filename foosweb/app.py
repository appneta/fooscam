from flask import Flask, redirect
from flask.ext.restful import Api
from flask.ext.assets import Environment, Bundle

from views import LiveHistory, Score, Players, Status
from foosweb import GameWatch

app = Flask(__name__)
api = Api(app)
api.add_resource(Score, '/score', endpoint = 'score')
api.add_resource(Players, '/players', endpoint = 'players')
api.add_resource(Status, '/status', endpoint = 'status')
api.add_resource(LiveHistory, '/livehistjson', endpoint = 'livehistjson')

assets = Environment(app)
js = Bundle('js/foosview.js', 'js/modernizr-2.6.2.min.js')
css = Bundle('css/normalize.css', 'css/main.css', 'css/foosview.css')
assets.register('css', css)
assets.register('js', js)

@app.route('/')
def home():
    return render_template('index.html')#, debug_image='static/img/table.png')

@app.route('/history')
def live_hist():
    return redirect(url_for('static', filename='history.html'))

@app.route('/readme')
def readme():
    return redirect(url_for('static', filename='fooscam.html'))

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)
    #uncomment to build db from scratch
    #db = create_engine('sqlite:///foosball.db')
    #ORMBase.metadata.create_all(db)
