from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from twisted.internet.task import LoopingCall
from twisted.internet import reactor

import json
import random
import requests
from pprint import pprint
import pdb
import os
import logging

db = create_engine('sqlite:///foosball.db')

ORMBase = declarative_base()

class Player(ORMBase):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Player('%s', '%s)" % (self.id, self.name)

class Game(ORMBase):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    red_off = Column(Integer)
    red_def = Column(Integer)
    blue_off = Column(Integer)
    blue_def = Column(Integer)
    winner = Column(String)
    blue_score = Column(Integer)
    red_score = Column(Integer)

    def __init__(self, winner, blue_score, red_score, red_off=1, red_def=1, blue_off=1, blue_def=1):
        self.red_off = red_off
        self.red_def = red_def
        self.blue_off = blue_off
        self.blue_def = blue_def
        self.winner = winner
        self.blue_score = blue_score
        self.red_score = red_score

class GameWatcher():

    debug=False
    log = logging.getLogger(__name__)

    players = [{'pos': 'blue_off','id': 1, 'name': '', 'lost_ticks': 0}, \
         {'pos': 'blue_def', 'id': 1, 'name': '', 'lost_ticks': 0}, \
         {'pos': 'red_off', 'id': 1, 'name': '', 'lost_ticks': 0}, \
         {'pos': 'red_def', 'id': 1, 'name': '', 'lost_ticks': 0}]

    announcements = ['A mighty battle is brewing', \
        "What time is it? (awyeah) it's FOOS TIME", \
        "It's a throw down, a show down, hell no we won't slow down, it's gonna GO DOWN", \
        "This is the ultimate show down of ultimate history", \
        'Autobots ... ASSEMBLE', \
        "C'mon you apes, you wanna live forever? Foos it up", \
        "Perhaps today IS a good day for foos", \
        "Yipee kaiyay motherfooser, GAME TIME", \
        "Cry havoc and let slip the balls of foos", \
        "A day may come when we forsake our foosball, but it IS NOT THIS DAY! This day we foos"]

    game_on = False
    found_player_count = 0
    players_lost_for_ticks = 0
    lost_tick_threshold = 3

    hipchat_api_key = os.environ.get('HIPCHAT_API_KEY')
    hipchat_room_id = os.environ.get('HIPCHAT_ROOM_ID')
    hipchat_url = 'https://api.hipchat.com/v1/rooms/message?auth_token='

    def __init__(self):
        self.log.setLevel(logging.DEBUG)
        fh = logging.StreamHandler()
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.log.addHandler(fh)
        self.log.info('Startup')

        """if self.hipchat_api_key is None or self.hipchat_room_id is None:
            self.log.warn('Hipchat env variables missing, disabling messaging')
            self.hipchat_url = ''
            self.hipchat_api_key = ''
            self.hipchat_room_id = ''
        else:""" #TODO: UNFUCK THIS
        self.hipchat_url += self.hipchat_api_key
        self.hipchat_url += '&room_id=' + str(self.hipchat_room_id) + '&from=Fooscam&message='
        #set up db connection
        Session = sessionmaker()
        Session.configure(bind=db)
        self.session = Session()

        #twisted event firing
        lc = LoopingCall(self.WatchTable)
        lc.start(2)
        reactor.run()

    def GetPlayers(self):
        """
        read and parse the JSON produced by detectPlayers
        """
        if self.debug:
            self.log.debug('Reading test/players.json')
            playerfile = 'test/players.json'
        else:
            playerfile = '/tmp/players.json'
        with open(playerfile) as f:
            players_json = f.read()

        current_players = json.loads(players_json)

        #sanity check and chop json
        if 'team' in current_players:
            if len(current_players['team']) == 2:
                if 'blue' in current_players['team'][0]:
                    #trace the number of ticks each player id goes unrecognized by detectPlayers during a game
                    if int(current_players['team'][0]['blue']['offense']) == -1 and self.game_on:
                        self.players[0]['lost_ticks'] += 1
                    else:
                        self.players[0]['lost_ticks'] = 0

                    #grab the player id
                    self.players[0]['id'] = current_players['team'][0]['blue']['offense']

                    if int(current_players['team'][0]['blue']['defense']) == -1 and self.game_on:
                        self.players[1]['lost_ticks'] += 1
                    else:
                        self.players[1]['lost_ticks'] = 0

                    self.players[1]['id'] = current_players['team'][0]['blue']['defense']

                if 'red' in current_players['team'][1]:
                    if int(current_players['team'][1]['red']['offense']) == -1 and self.game_on:
                        self.players[2]['lost_ticks'] += 1
                    else:
                        self.players[2]['lost_ticks'] = 0

                    self.players[2]['id'] = current_players['team'][1]['red']['offense']

                    if int(current_players['team'][1]['red']['defense']) == -1 and self.game_on:
                        self.players[3]['lost_ticks'] += 1
                    else:
                        self.players[3]['lost_ticks'] = 0

                    self.players[3]['id'] = current_players['team'][1]['red']['defense']

    def GetFriendlyJSON(self):
        """
        return JSON formatted string with friendly names in place of player ID numbers detected by detectPlayers
        """
        self.GetPlayers()
        self.found_player_count = 0

        for player in self.players:
            player_name = self.GetPlayerName(player['id'])
            #wait a few ticks after a player becomes unrecognized before marking them as lost
            if player_name is None or player['id'] == '-1':
                if player['lost_ticks'] > self.lost_tick_threshold:
                    player['name'] = 'None'
            else:
                self.found_player_count += 1
                player['name'] = player_name.name


        new_json = {'team' : [{'blue': {'offense': self.players[0]['name'], 'defense': self.players[1]['name']}}, \
            {'red': {'offense': self.players[2]['name'], 'defense': self.players[3]['name']}}]}

        return json.dumps(new_json)

    def GetPlayerName(self, player_id):
        """
        return player name from db by id
        """
        return self.session.query(Player).filter_by(id=player_id).first()

    def WatchTable(self):

        friendly_json = self.GetFriendlyJSON()

        #total the number of ticks we've lost players
        for player in self.players:
            self.players_lost_for_ticks += player['lost_ticks']

        if self.players_lost_for_ticks > 0:
            self.log.debug('Players lost, tick counter at: ' + str(self.players_lost_for_ticks))

        if self.game_on:
            self.log.debug('game is on')

            with open('friendly_names.json','w') as f:
                f.write(friendly_json)

            if self.found_player_count < 4:
                self.players_lost_for_ticks += 1
                #TODO: this threshold is pretty damn arbitrary ...
                if self.players_lost_for_ticks > 10:
                    #we've lost track of one player for four ticks or more players for less ticks ...
                    self.game_on = False
                    self.log.info('game is over')
                    self.players_lost_for_ticks = 0
        else:
            self.log.debug('waiting for a game to start ...')
            if self.found_player_count == 4:
                self.game_on = True
                self.log.info('game is starting')
                hipchat_message = ' with ' + self.players[0]['name'] + ', ' + self.players[1]['name'] \
                    + ', ' + self.players[2]['name'] + ', and ' + self.players[3]['name'] + '!'

                url = self.hipchat_url+random.choice(self.announcements) + hipchat_message
                if self.debug == False and url != '':
                    self.log.debug('sending hipchat update to: ' + url)
                    r = requests.get(url)
                    self.log.debug('http resp: ' + str(r.status_code))
                else:
                    self.log.debug('skipping hipchat call to: ' + url)


if __name__ == '__main__':
    gw = GameWatcher()
