from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

ORMBase = declarative_base()

#DB ORM models

class Player(ORMBase):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    authenticated = Column(Boolean)

    def __init__(self, name):
        self.name = name

    def is_active(self):
        return True

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

class GameState(ORMBase):
    __tablename__ = 'state'
    id = Column(Integer, primary_key=True)
    game_on = Column(Boolean)
    red_off = Column(Integer, ForeignKey(Player.id), nullable=False)
    red_def = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_off = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_def = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_score = Column(Integer)
    red_score = Column(Integer)
    game_started = Column(Integer)
    fuzzy = Column(Boolean)
    game_winner = Column(String)

    def __init__(self):
        self.id = 1
        self.game_on = False
        self.red_off = -1
        self.red_def = -1
        self.blue_off = -1
        self.blue_def = -1
        self.fuzzy = 0
        self.game_started = 0
        self.game_winner = ''

class Game(ORMBase):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    red_off = Column(Integer, ForeignKey(Player.id), nullable=False)
    red_def = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_off = Column(Integer, ForeignKey(Player.id), nullable=False)
    blue_def = Column(Integer, ForeignKey(Player.id), nullable=False)
    winner = Column(String)
    blue_score = Column(Integer)
    red_score = Column(Integer)
    started = Column(Integer)
    ended = Column(Integer)

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

class Team(ORMBase):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    player_one = Column(Integer, ForeignKey(Player.id), nullable=False)
    player_two = Column(Integer, ForeignKey(Player.id), nullable=False)
    name = Column(String, nullable=False)
    status = Column(Integer, nullable=False)

    STATUS_PENDING = 1
    STATUS_COMPLETE = 2
    STATUS_DECLINED = 3
    STATUS_CANCELLED = 4

    def __init__(self, player_one, player_two, name):
        self.status = self.STATUS_PENDING
        self.player_one = player_one
        self.player_two = player_two
        self.name = name

class Admin(ORMBase):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey(Player.id), nullable=False)
