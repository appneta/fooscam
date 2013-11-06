from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db = create_engine('sqlite:///foosball.db')
Session = sessionmaker()
Session.configure(bind=db)

def get_db_session():
    return Session()
