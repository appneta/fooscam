from flask import current_app
from flask.ext.login import current_user
from flask.ext.mail import Message
from foosweb.models import Player, PasswordReset
from foosweb.app import db

import os
from hashlib import md5

import pdb
import logging
log = logging.getLogger('gamewatch')

class Auth():
    def _is_admin(self, user_id):
        try:
            user_id = int(user_id)
        except ValueError, e:
            return

        try:
            admin = self.session.query(Admin).filter_by(player_id=user_id).one()
        except NoResultFound:
            return
        except Exception, e:
            log.error('Exception %s thrown checking admin status of %s!' % (repr(e), str(user_id)))
            return

        if admin is not None:
            return True

    def _make_pw_reset_link(self, user_id, server_name):

        reset_hash = "%s%s" % (md5(os.urandom(8)).hexdigest(), md5(os.urandom(8)).hexdigest())

        pw_reset = None

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

        mail = current_app.extensions['mail']
        server_name = current_app.config['SERVER_NAME']

        player = self.GetPlayerByEmail(user_email)
        if player is not None:
            reset_link = self._make_pw_reset_link(player.id, server_name)
        else:
            log.debug('player %s not found in player db' % (user_email))
            return
        msg = Message(subject='Foosview password reset', recipients = [user_email],\
            body='Your Foosview password reset link is %s' % (reset_link))

        try:
            mail.send(msg)
        except Exception, e:
            log.error('Exception %s sending password reset email to %s' % (repr(e), player.email))
            return

        return True

    def GetPlayerByResetHash(self, reset_hash):
        pass_reset = None

        try:
            pass_reset = self.session.query(PasswordReset).filter(PasswordReset.reset_hash == reset_hash).one()
        except NoResultFound:
            return

        if pass_reset is not None:
            return self.GetPlayerByID(pass_reset.player_id)

    def InvalidatePasswordResets(self, player_id):
        self.session.query(PasswordReset).filter(PasswordReset.player_id == player_id).delete()
        self.session.commit()

    def GetPlayerByEmail(self, email):
        email = str(email).strip().lower()
        player = Player.query.filter_by(email=email).first()
        return player

    def GetPlayerByID(self, player_id):
        try:
            id = int(player_id)
        except ValueError, e:
            return

        try:
            player = self.session.query(Player).filter_by(id=player_id).one()
        except NoResultFound:
            return
        except Exception, e:
            log.error('Exception thrown trying to get player %s!' % (str(player_id)))
            return

        return player

    @classmethod
    def RequiresAdmin(cls, func):
        """decorator to protect views to admins only"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            db_session = get_db_session()
            if current_user.is_authenticated():
                try:
                    admin = db_session.query(Admin).filter_by(player_id = current_user.id).one()
                except NoResultFound:
                    return redirect(url_for('FoosView:index'))
                except Exception, e:
                    log.error('Exception %s thrown checking admin status of %s!' % (repr(e), str(id)))
                    return redirect(url_for('FoosView:index'))
                if admin is not None:
                    return func(*args, **kwargs)
            return redirect(url_for('FoosView:index'))
        return wrapper
