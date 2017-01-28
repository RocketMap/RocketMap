import unittest
from pogom import utils


class UtilsTest(unittest.TestCase):
    def test_get_pokemon_id(self):
        self.assertEqual(1, utils.get_pokemon_id("Bulbasaur"))
        self.assertEqual(149, utils.get_pokemon_id("Dragonite"))

        # Unknown name returns -1
        self.assertEqual(-1, utils.get_pokemon_id("Unknown"))

    def test_get_pokemon_name(self):
        self.assertEqual("Bulbasaur", utils.get_pokemon_name(1))
        self.assertEqual("Dragonite", utils.get_pokemon_name(149))

        # Unknown ID raises KeyError
        self.assertRaises(KeyError, utils.get_pokemon_name, 12367)
