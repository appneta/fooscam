import os

class Config(object):
    DEBUG = False
    TESTING = False
    DATABASE_URI = 'sqlite:///foosball.db'

class Dev(Config):
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
