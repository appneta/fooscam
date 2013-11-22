from foosweb.app import db

class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean)
    challonge_id = db.Column(db.String)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
        self.challonge_id = ''
        self.authenticated = False

    def is_active(self):
        return True

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

class GameState(db.Model):
    __tablename__ = 'state'
    id = db.Column(db.Integer, primary_key=True)
    game_on = db.Column(db.Boolean)
    red_off = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    red_def = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    blue_off = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    blue_def = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    blue_score = db.Column(db.Integer)
    red_score = db.Column(db.Integer)
    game_started = db.Column(db.Integer)
    fuzzy = db.Column(db.Boolean)
    game_winner = db.Column(db.String)
    red_team = db.Column(db.String)
    blue_team = db.Column(db.String)

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
        self.red_team = ''
        self.blue_team = ''

class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    red_off = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    red_def = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    blue_off = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    blue_def = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    winner = db.Column(db.String)
    blue_score = db.Column(db.Integer)
    red_score = db.Column(db.Integer)
    started = db.Column(db.Integer)
    ended = db.Column(db.Integer)

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    player_one = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    player_two = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    name = db.Column(db.String, nullable=False)
    status = db.Column(db.Integer, nullable=False)

    STATUS_PENDING = 1
    STATUS_COMPLETE = 2
    STATUS_DECLINED = 3
    STATUS_CANCELLED = 4

    def __init__(self, player_one, player_two, name):
        self.status = self.STATUS_PENDING
        self.player_one = player_one
        self.player_two = player_two
        self.name = name

class PasswordReset(db.Model):
    __tablename__ = 'pw_resets'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)
    reset_hash = db.Column(db.String, nullable=False)

    def __init__(self, player_id, reset_hash):
        self.player_id = player_id
        self.reset_hash = reset_hash

class Tournaments(db.Model):
    __tablename__ = 'tournaments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey(Player.id), nullable=False)

def init_db():
    db.create_all()
    init_state = GameState()
    anon_player = Player('Anonymous', 'anon@anon.com', '')
    anon_player.id = 0
    db.session.add(init_state)
    db.session.add(anon_player)
    db.session.commit()
