from foosweb.app import db
from foosweb.models import GameState, Player, Game
from foosweb.controllers.team import TeamData

from flask import current_app, g
from datetime import datetime
import os
from time import time
import pdb


class GameWatch():
    """
    main game logic lives in here
    """
    def __init__(self):

        #persist current game state by maintaining only 1 row in there
        self.game_state = GameState.query.filter_by(id=1).first()

        #reset fuzziness between games
        if not self.game_state.game_on:
            if self.game_state.fuzzy:
                self.game_state.fuzzy = False
                self.CommitState()

        #if a game winner has been decided clear from the game state after a short time
        if self.game_state.game_winner != '':
            winner_announced_at = Game.query.with_entities(Game.ended).order_by(Game.id.desc()).first()
            if len(winner_announced_at) == 1:
                announce_duration = datetime.fromtimestamp(time()) - datetime.fromtimestamp(winner_announced_at[0])
                if announce_duration.seconds > 2:
                    self.game_state.game_winner = ''
                    self.CommitState()

    def UpdatePlayers(self, players):
        """
        do something constructive with the incoming player ID's
        """
        new_ids = [players['bo'], players['bd'], players['ro'], players['rd']]
        tmp_ids = self.CurrentPlayerIDs()
        current_ids = [tmp_ids['bo'], tmp_ids['bd'], tmp_ids['ro'], tmp_ids['rd']]

        #same as it ever was
        if new_ids == current_ids:
            if self.game_state.fuzzy:
                current_app.logger.debug('got 4 players matching ids for fuzzy game in progress, reverting fuzzy state')
                self.game_state.fuzzy = False
                self.CommitState()
                return

        #if there was a game on, there ain't now
        if new_ids == [-1, -1, -1,-1]:
            if self.game_state.game_on:
                current_app.logger.debug("got 4 unknown ID's, ending current game")
                self.GameOver()
                return
            else:
                #if there isn't a game on, who cares?
                return

        #one or more incoming ID's are unknown (but not all of them)
        if new_ids != current_ids and (-1 in new_ids):
            if self.game_state.game_on:
                #mark current game fuzzy
                self.game_state.fuzzy = True
                self.CommitState()
                current_app.logger.debug('fuzzy players detected, ignoring player ids')
                for pair in zip(current_ids, new_ids):
                    if pair[0] != pair[1] and pair[1] != -1:
                        #game is fuzzy AND a valid player id has changed!
                        current_app.logger.debug('fuzzy game with people moving around, assuming game over')
                        self.GameOver()
                        return
            else:
                #fuzzy players detected but no game is on
                return
        else:
            #id change detected and all id's are known
            if not self.game_state.game_on:
                current_app.logger.debug('4 new ids locked and no game going ... starting a new game!')
                g.current_players = players

                self.game_state.blue_off = players['bo']
                self.game_state.blue_def = players['bd']
                self.game_state.red_off = players['ro']
                self.game_state.red_def = players['rd']

                td = TeamData()
                red_team = td._get_team_name_by_ids(players['ro'], players['rd'])
                blue_team = td._get_team_name_by_ids(players['bo'], players['bd'])

                self.CommitState()
                self.GameOn()
            else:
                #TODO: something useful here?
                current_app.logger.debug('4 new ids locked but game is already going, throwing away current game state and starting a new game')


    def UpdateScore(self, red_score, blue_score):
        """
        do something useful with the score
        """
        if not self.game_state.game_on:
            #ignoring score update while no game underway
            return
        else:
            #processing score update while game underway
            current_app.logger.debug('new red: %s new blue: %s -- old red: %s old blue: %s' % (str(red_score), str(blue_score),\
                str(self.game_state.red_score), str(self.game_state.blue_score)))
            #end the game when a score goes from >= 8 to 0
            if (red_score == 0 and self.game_state.red_score >=8) or (blue_score == 0 and self.game_state.blue_score >=8):
                current_app.logger.debug('score went from red: ' + str(self.game_state.red_score) + ' blue: ' + str(self.game_state.blue_score) + ' to red: ' + \
                    str(red_score) + ' blue: ' + str(blue_score))
                current_app.logger.debug('assuming game is over and using previous scores to determine winner')
                self.GameOver()
                return
            else:
                if self.game_state.fuzzy:
                    current_app.logger.debug('minor score change detected and game is fuzzy, ignoring until locked')
                    return
                else:
                    current_app.logger.debug('minor score change detected and game is locked, updating score')
                    self.game_state.red_score = red_score
                    self.game_state.blue_score = blue_score
                    self.CommitState()
                    if red_score == 10 or blue_score == 10:
                        self.GameOver()
                    return

    def CurrentPlayerIDs(self):
        return {'bo': self.game_state.blue_off, 'bd': self.game_state.blue_def, 'ro': self.game_state.red_off, 'rd': self.game_state.red_def}

    def GetScore(self):
        return self.game_state.red_score,  self.game_state.blue_score

    def IsGameOn(self):
        return self.game_state.game_on

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

        db.session.add(foos_log)
        db.session.commit()

        #set a state object to the winner to update web ui with winning team detected
        self.game_state.game_winner = winner

        self.game_state.game_on = False
        self.game_state.blue_off = -1
        self.game_state.blue_def = -1
        self.game_state.red_off = -1
        self.game_state.red_def = -1
        self.CommitState()

    def GameOn(self):
        #TODO: this method should accept 4 player ID's
        self.game_state.game_on = True
        self.game_state.fuzzy = False
        self.game_state.red_score = 0
        self.game_state.blue_score = 0
        self.game_state.game_started = int(time())
        self.CommitState()

    def CommitState(self, state=None):
        if state == None:
            db.session.add(self.game_state)
        else:
            db.session.add(state)
        db.session.commit()
