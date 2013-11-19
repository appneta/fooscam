from foosweb.app import app
if app.config['DEBUG']:
    app.run(host='0.0.0.0')
else:
    app.run()
