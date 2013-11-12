class Config(object):
    DEBUG = False
    TESTING = False

class Dev(Config):
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'foosview@gmail.com'
    MAIL_PASSWORD = 'labrat1214'
    MAIL_DEFAULT_SENDER = 'foosview@gmail.com'
    SERVER_NAME = 'localhost:5000'
