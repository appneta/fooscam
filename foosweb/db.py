from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db = create_engine('sqlite:///foosball.db')
Session = sessionmaker()
Session.configure(bind=db)

fv_session = Session()

def get_db_session():
    return fv_session
