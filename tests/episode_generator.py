import unittest
import sys
import os
sys.path.append(os.path.abspath(".."))
from market_emulator.episode_generator import EpisodeGenerator
import logging

class EpisodeGeneratorTestCase (unittest.TestCase):
    def setUp (self):
        self.eg = EpisodeGenerator ('BTC_ETH', '../fragments/', 180000)

    def test_random_episode (self):
        for i in range(0, 10):
            e = self.eg.get_random_episode()
            logging.error ('i='+str(i)+' fstart='+str(e.fstart)+' start='+str(e.f.start)+' end='+str(e.f.end))

if __name__ == '__main__':
    unittest.main()
