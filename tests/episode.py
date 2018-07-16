import unittest
import sys
import os
sys.path.append(os.path.abspath(".."))
from market_emulator.episode import Episode
#from market_emulator.episode_generator import EpisodeGenerator
from market_emulator.fragment import Fragment
import logging

class EpisodeTestCase (unittest.TestCase):
    def setUp (self):
        self.e = Episode ('../fragments/BTC_ETH/1530224638648.pickle', 1000000, 180000)

    def test_limit_order (self):
        pass

    def test_market_order (self):
        pass

if __name__ == '__main__':
    unittest.main()
