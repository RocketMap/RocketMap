import unittest
import os
from pogom import utils


# Mock get_args function to work with tests
class Args:
    locale = 'en'
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    data_dir = 'static/dist/data'
    locales_dir = 'static/dist/locales'


def mock_get_args():
    return Args()


utils.get_args = mock_get_args


class UtilsTest(unittest.TestCase):

    def test_get_pokemon_name(self):
        self.assertEqual("Bulbasaur", utils.get_pokemon_name(1))
        self.assertEqual("Dragonite", utils.get_pokemon_name(149))

        # Unknown ID raises KeyError
        self.assertRaises(KeyError, utils.get_pokemon_name, 12367)
