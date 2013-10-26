from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

ORMBase = declarative_base()

#DB ORM models

class Player(ORMBase):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, name):
        self.name = name

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