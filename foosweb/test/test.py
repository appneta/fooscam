import unittest
import pdb
from foosweb.app import app

class FoosTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True

    def tearDown(self):
        pass

    def test_something(self):
        pass
