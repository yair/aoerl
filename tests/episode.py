import unittest
import sys
import os
sys.path.append(os.path.abspath(".."))
from market_emulator.episode import Episode
from market_emulator.fragment import Fragment
import logging

class EpisodeTestCase (unittest.TestCase):
    def setUp (self):
        self.e = Episode ('../fragments/BTC_ETH/1530224638648.pickle', 1000000, 180000)

    def test_episode...
    def test_random_episode (self):
        for i in range(0, 10):
            e = self.eg.get_random_episode()
            logging.error ('i='+str(i)+' fstart='+str(e.fstart)+' start='+str(e.f.start)+' end='+str(e.f.end))

if __name__ == '__main__':
    unittest.main()
