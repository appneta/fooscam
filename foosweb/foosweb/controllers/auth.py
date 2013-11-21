from flask import current_app
from flask.ext.login import current_user
from flask.ext.mail import Message
from foosweb.models import Player, PasswordReset, Admin
from foosweb.app import db

import os
from hashlib import md5

import pdb

class Auth():
    def _is_admin(self, user_id):
        try:
            user_id = int(user_id)
        except ValueError, e:
            return

        admin = Admin.query.filter_by(player_id=user_id).first()
        if admin is not None:
            return True

    def _make_pw_reset_link(self, user_id, server_name):

        reset_hash = "%s%s" % (md5(os.urandom(8)).hexdigest(), md5(os.urandom(8)).hexdigest())

        pw_reset = PasswordReset.query.filter_by(player_id = user_id).first()

        if pw_reset is None:
            pw_reset = PasswordReset(user_id, reset_hash)
        else:
            pw_reset.reset_hash = reset_hash

        db.session.add(pw_reset)
        db.session.commit()

        reset_link = 'http://%s/pw_reset/%s' % (server_name, reset_hash)
        return reset_link

    @classmethod
    def Login(self, player):
        player.authenticated = True
        db.session.add(player)
        db.session.commit()

    @classmethod
    def Logout(self, current_player):
        current_player.authenticated = False
        db.session.add(current_player)
        db.session.commit()

    def ForgotPassword(self, user_email):
        pdb.set_trace()

        mail = current_app.extensions['mail']
        server_name = current_app.config['SERVER_NAME']

        #for testing
        if server_name == '':
            server_name = 'localhost'

        player = self.GetPlayerByEmail(user_email)
        if player is not None:
            reset_link = self._make_pw_reset_link(player.id, server_name)
        else:
            current_app.logger.debug('player %s not found in player db' % (user_email))
            return
        msg = Message(subject='Foosview password reset', recipients = [user_email],\
            body='Your Foosview password reset link is %s' % (reset_link))

        try:
            mail.send(msg)
        except Exception, e:
            current_app.logger.error('Exception %s sending password reset email to %s' % (repr(e), player.email))
            return

        return True

    def GetPlayerByResetHash(self, reset_hash):
        pass_reset = None

        pass_reset = PasswordReset.query.filter(PasswordReset.reset_hash == reset_hash).first()

        if pass_reset is not None:
            return self.GetPlayerByID(pass_reset.player_id)

    def InvalidatePasswordResets(self, player_id):
        PasswordReset.query.filter(PasswordReset.player_id == player_id).delete()
        db.session.commit()

    def GetPlayerByEmail(self, email):
        email = str(email).strip().lower()
        player = Player.query.filter_by(email=email).first()
        return player

    def GetPlayerByID(self, player_id):
        try:
            id = int(player_id)
        except ValueError, e:
            return

        player = Player.query.filter_by(id=player_id).one()

        return player

    @classmethod
    def RequiresAdmin(cls, func):
        """decorator to protect views to admins only"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            db_session = get_db_session()
            if current_user.is_authenticated():
                admin = Admin.query.filter_by(player_id = current_user.id).one()
                if admin is not None:
                    return func(*args, **kwargs)
            return redirect(url_for('foos.index'))
        return wrapper
