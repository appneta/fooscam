from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.declarative import declarative_base

from models import GameState, Player, Game, ORMBase

import json
import os
from time import time
from datetime import datetime, timedelta

import logging

import pdb

log = logging.getLogger('gamewatch')

class GameWatch():
    """
    main game logic lives in here
    """
    def __init__(self):
        db = create_engine('sqlite:///foosball.db')
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()

        if not os.path.exists('./foosball.db'):
            self.InitializeDB(db)

        #persist current game state by maintaining only 1 row in there
        self.game_state = self.session.query(GameState).filter_by(id=1).first()

        #reset fuzziness between games
        if not self.game_state.game_on:
            self.game_state.fuzzy = False
            self.CommitState()

        #if a game winner has been decided clear from the game state after a short time
        if self.game_state.game_winner != '':
            winner_announced_at = self.session.query(Game.ended).order_by(Game.id.desc()).first()
            if len(winner_announced_at) == 1:
                announce_duration = datetime.fromtimestamp(time()) - datetime.fromtimestamp(winner_announced_at[0])
                if announce_duration.seconds > 2:
                    self.game_state.game_winner = ''
                    self.CommitState()

    def InitializeDB(self, db_obj):
        """build default sqlite database"""
        ORMBase.metadata.create_all(db_obj)
        init_state = GameState()
        self.CommitState(init_state)
        anon_player = Player('Anonymous')
        anon_player.id = -1
        self.session.add(anon_player)
        self.session.commit()

    def UpdatePlayers(self, players):
        """
        do something constructive with the incoming player ID's
        """
        new_ids = [players['bo'], players['bd'], players['ro'], players['rd']]
        tmp_ids = self.GetIDs()
        current_ids = [tmp_ids['bo'], tmp_ids['bd'], tmp_ids['ro'], tmp_ids['rd']]

        #same as it ever was
        if new_ids == current_ids:
            if self.game_state.fuzzy:
                log.debug('got 4 players matching ids for game in progress, reverting fuzzy state')
                self.game_state.fuzzy = False
                self.CommitState()
                return

        #if there was a game on, there ain't now
        if new_ids == [-1, -1, -1,-1]:
            if self.game_state.game_on:
                log.debug("got 4 unknown ID's, ending current game")
                self.GameOver()
                return
            else:
                #if there isn't a game on, who cares?
                log.debug("got 4 unknown ID's, no game to end")
                return

        #one or more incoming ID's are unknown (but not all of them)
        if new_ids != current_ids and (-1 in new_ids):
            if self.game_state.game_on:
                #mark current game fuzzy
                self.game_state.fuzzy = True
                self.CommitState()
                log.debug('fuzzy players detected, ignoring player ids')
                for pair in zip(current_ids, new_ids):
                    if pair[0] != pair[1] and pair[1] != -1:
                        #game is fuzzy AND a valid player id has changed!
                        log.debug('fuzzy game with people moving around, assuming game over')
                        self.GameOver()
                        return
            else:
                log.debug('fuzzy players detected but no game is on')
                return
        else:
            #id change detected and all id's are known
            #TODO: this is ugly flow control
            if not self.game_state.game_on:
                log.debug('4 new ids locked and no game going ... starting a new game!')
            else:
                #TODO: something useful here?
                log.debug('4 new ids locked but game is already going, throwing away current game state and starting a new game')


            self.game_state.blue_off = players['bo']
            self.game_state.blue_def = players['bd']
            self.game_state.red_off = players['ro']
            self.game_state.red_def = players['rd']
            self.CommitState()
            self.GameOn()

    def UpdateScore(self, score):
        """
        do something useful with the score
        """

        if not self.game_state.game_on:
            log.debug('ignoring score update while no game underway')
            return
        else:
            log.debug('processing score update while game underway')
            log.debug(str(score['red']) + ' ' + str(self.game_state.red_score) + ' ' + str(score['blue']) + ' ' + str( self.game_state.blue_score))
            #end the game when a score goes from >= 8 to 0
            if (score['red'] == 0 and self.game_state.red_score >=8) or (score['blue'] == 0 and self.game_state.blue_score >=8):
                log.debug('score went from red: ' + str(self.game_state.red_score) + ' blue: ' + str(self.game_state.blue_score) + ' to red: ' + \
                    str(score['red']) + ' blue: ' + str(score['blue']))
                log.debug('assuming game is over and using previous scores to determine winner')
                self.GameOver()
                return
            else:
                if self.game_state.fuzzy:
                    log.debug('minor score change detected and game is fuzzy, ignoring until locked')
                    return
                else:
                    log.debug('minor score change detected and game is locked, updating score')
                    self.game_state.red_score = score['red']
                    self.game_state.blue_score = score['blue']
                    self.CommitState()
                    return

    def GetScore(self):
        return self.game_state.red_score,  self.game_state.blue_score

    def IsGameOn(self):
        return self.game_state.game_on

    def GetNames(self):
        player_names = {}

        player_names['bo'] = self.GetNameByID(self.game_state.blue_off)
        player_names['bd'] = self.GetNameByID(self.game_state.blue_def)
        player_names['ro'] = self.GetNameByID(self.game_state.red_off)
        player_names['rd'] = self.GetNameByID(self.game_state.red_def)

        return player_names

    def GetIDs(self):
        #return [self.game_state.blue_off, self.game_state.blue_def, self.game_state.red_off, self.game_state.red_def]
        player_ids = {}
        player_ids['bo'] = self.game_state.blue_off
        player_ids['bd'] = self.game_state.blue_def
        player_ids['ro'] = self.game_state.red_off
        player_ids['rd'] = self.game_state.red_def
        return player_ids

    def GetNameByID(self, player_id):
        if player_id == -1:
            player_name = 'None'
        else:
            try:
                player_name = str(self.session.query(Player.name).filter_by(id=player_id).one()[0])
            except NoResultFound:
                player_name = 'Anonymous'

        return player_name

    def GetHistory(self):
        game_history = []
        for game in self.session.query(Game).order_by(Game.id):
            game_history.append(game)

        return game_history

    def GetWinner(self):
        if self.game_state.game_winner == '':
            return None
        else:
            return self.game_state.game_winner

    def GameOver(self):
        """
        determine the winner and record that along with the current game state
        """

        #decide who won and compensate for players not actually sliding the 10th cube into place
        if self.game_state.red_score > self.game_state.blue_score:
            winner = 'red'
            self.game_state.red_score = 10
        elif self.game_state.blue_score > self.game_state.red_score:
            winner = 'blue'
            self.game_state.blue_score = 10
        elif self.game_state.blue_score == self.game_state.red_score:
            winner = 'tie'

        #populate and commit a game state object
        foos_log = Game(winner=winner,\
            blue_score=self.game_state.blue_score,\
            red_score=self.game_state.red_score,\
            red_off=self.game_state.red_off,\
            red_def=self.game_state.red_def,\
            blue_off=self.game_state.blue_off,\
            blue_def=self.game_state.blue_def,\
            started=self.game_state.game_started,\
            ended=int(time()))

        self.session.add(foos_log)
        self.session.commit()

        #set a state object to the winner to update web ui with winning team detected
        self.game_state.game_winner = winner

        self.game_state.game_on = False
        self.game_state.blue_off = -1
        self.game_state.blue_def = -1
        self.game_state.red_off = -1
        self.game_state.red_def = -1
        self.CommitState()

    def GameOn(self):
        self.game_state.game_on = True
        self.game_state.fuzzy = False
        self.game_state.red_score = 0
        self.game_state.blue_score = 0
        self.game_state.game_started = int(time())
        self.CommitState()

    def CommitState(self, state=None):
        if state == None:
            self.session.add(self.game_state)
        else:
            self.session.add(state)
        self.session.commit()

