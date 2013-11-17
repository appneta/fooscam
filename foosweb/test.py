import unittest
import json
import pdb
from foosweb.app import app, db
from foosweb.models import init_db

class FoosTest(unittest.TestCase):
    def setUp(self):
        app.config.from_object('config.Test')
        self.app = app.test_client()
        init_db()

    def tearDown(self):
        db.drop_all()

    def login(self, default=False, email=None, password=None):
        if default:
            email='email@host.com'
            password='secret'
        return self.app.post('/login', data=dict(email=email, password=password), follow_redirects=True)

    def signup(self, default=False, email=None, password=None, name=None):
        if default:
            email = 'email@host.com'
            password = 'secret'
            name = 'someone'

        return self.app.post('/players/signup', data=dict(
            name=name,
            email=email,
            password=password,
            confirm_pass=password), follow_redirects=True)

    def test_invalid_login(self):
        rv = self.login(email='x@y.com', password='x')
        self.assertTrue('Invalid' in rv.data)

    def test_signup(self):
        rv = self.signup(default=True)
        self.assertTrue('Welcome' in rv.data)

    def test_signup_existing_name(self):
        self.signup('dude@thing1.com', 'secret', 'dude')
        rv = self.signup('dude@thing2.com', 'secret', 'dude')
        self.assertTrue('please choose another name' in rv.data)

    def test_signup_existing_email(self):
        self.signup('dude@thing.com', 'secret', 'dude1')
        rv = self.signup('dude@thing.com', 'secret', 'dude2')
        self.assertTrue('email address already exists' in rv.data)

    def test_login_logout(self):
        self.signup(default=True)
        rv = self.app.get('/logout', follow_redirects=True)
        self.assertTrue('Logged out' in rv.data)
        rv = self.login(email='email@host.com', password='secret')
        self.assertTrue('Welcome back' in rv.data)

    def test_update_email_password(self):
        self.signup(default=True)
        rv = self.app.post('/players/me/settings', data = dict(
            email = 'email@newhost.com',
            password = 'newpass',
            confirm_pass = 'newpass'), follow_redirects=True)
        self.assertTrue('Settings saved' in rv.data)
        self.app.get('/logout')
        rv = self.login(email='email@newhost.com', password='newpass')
        self.assertTrue('Welcome back' in rv.data)

    def test_player_list_view(self):
        self.signup(default=True)
        rv = self.app.get('/players/')
        self.assertTrue('/players/0' in rv.data)

    def test_send_teamup_invite(self):
        self.signup(default=True)
        self.app.get('/logout')
        self.signup(email='x@y.com', password='pass', name='person')
        rv = self.app.post('/teams/teamup/1', data = dict(team_name='team'), follow_redirects=True)
        self.assertTrue('has been invited' in rv.data)

    def test_view_sent_invite(self):
        self.signup(default=True)
        self.app.get('/logout')
        self.signup(email='x@y.com', password='pass', name='person')
        self.app.post('/teams/teamup/1', data = dict(team_name='team'), follow_redirects=True)
        rv = self.app.get('/teams/teamup/invites')
        self.assertTrue('Keep waiting for' in rv.data)

    def test_view_received_invite(self):
        self.signup(default=True)
        self.app.get('/logout')
        self.signup(email='x@y.com', password='pass', name='person')
        self.app.post('/teams/teamup/1', data = dict(team_name='team'), follow_redirects=True)
        self.app.get('/logout')
        self.login(default=True)
        rv = self.app.get('/teams/teamup/invites')
        self.assertTrue('Join person on team team' in rv.data)

    def test_accept_received_invite(self):
        self.signup(default=True)
        self.app.get('/logout')
        self.signup(email='x@y.com', password='pass', name='person')
        self.app.post('/teams/teamup/1', data = dict(team_name='team'), follow_redirects=True)
        self.app.get('/logout')
        self.login(default=True)
        rv = self.app.get('/teams/teamup/accept/1', follow_redirects=True)
        self.assertTrue('teamed up' in rv.data)

    def test_empty_teams(self):
        rv = self.app.get('/teams/')
        self.assertTrue('Not even ONE team' in rv.data)

    def test_team_list(self):
        self.signup(default=True)
        self.app.get('/logout')
        self.signup(email='x@y.com', password='pass', name='person')
        self.app.post('/teams/teamup/1', data = dict(team_name='TeamName'), follow_redirects=True)
        self.app.get('/logout')
        self.login(default=True)
        self.app.get('/teams/teamup/accept/1', follow_redirects=True)
        rv = self.app.get('/teams/')
        self.assertTrue('TeamName' in rv.data)

    def test_game_status_off(self):
        rv = self.app.get('/status')
        rj = json.loads(rv.get_data())
        self.assertEqual(rj['status'], 'gameoff')

    def test_game_score_nil(self):
        rv = self.app.get('/score')
        rj = json.loads(rv.get_data())
        self.assertEqual(rj['score'], {'red': '', 'blue': ''})

    def test_game_players_nil(self):
        rv = self.app.get('/current_players')
        rj = json.loads(rv.get_data())
        nil_player = {"gravatar": "", "name": "None", "id": -1}
        self.assertEqual(rj['bo'], nil_player)
        self.assertEqual(rj['bd'], nil_player)
        self.assertEqual(rj['ro'], nil_player)
        self.assertEqual(rj['rd'], nil_player)

    def test_player_update_no_json(self):
        rv = self.app.post('/current_players', data = 'yodawg')
        self.assertEqual(rv.status_code, 400)
        self.assertTrue('data must be posted in json format' in rv.data)

    def test_player_update_bad_json(self):
        rv = self.app.post('/current_players', data = json.dumps({'thing' : 'stuff'}), content_type = 'application/json')
        self.assertEqual(rv.status_code, 400)
        self.assertTrue('no team key in json' in rv.data)

    def test_player_update_no_teams(self):
        rv = self.app.post('/current_players', data = json.dumps({'team' : 'stuff'}), content_type = 'application/json')
        self.assertEqual(rv.status_code, 400)
        self.assertTrue('ONLY two' in rv.data)
