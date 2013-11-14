from foosweb.app import db

class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    challonge_id = db.Column(db.String(120), unique=True)
    authenticated = db.Column(db.Boolean)
    #role = db.Column(db.SmallInteger, default=self.ROLE_PLAYER)
    #status = db.Column(db.SmallInteger, default=self.STATUS_NEW)

    ROLE_ADMIN = 0
    ROLE_PLAYER = 1
    STATUS_NEW = 0
    STATUS_ACTIVE = 1
    STATUS_DISABLED = 3

    def __init__(self, name=None, email=None, password=None):
        self.name = name
        self.email = email
        self.password = password

    def is_active(self):
        return True

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)
