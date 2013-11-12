from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import current_app

#TODO: I think flask-sql alchemy should fix this
#db = create_engine(current_app.config['DATABASE_URI'])
db = create_engine('sqlite:///foosball.db')
Session = sessionmaker()
Session.configure(bind=db)

fv_session = Session()

def get_db_session():
    return fv_session
