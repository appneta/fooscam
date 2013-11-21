import os

_basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'foosball.db')
    SECRET_KEY = 'too many secrets'
    FOOSVIEW_VERSION='0.2.2a'

class Dev(Config):
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_TLS = bool(os.getenv('MAIL_USE_TLS'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

class Prod(Config):
    SERVER_NAME= 'foosserv'
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_TLS = bool(os.getenv('MAIL_USE_TLS'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

class Test(Config):
    DEBUG = True
    TESTING = True
    HOST = '0.0.0.0'
    PORT = 5000
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
