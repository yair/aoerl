import unittest
import importlib
import sys
import os
sys.path.append(os.path.abspath(".."))
from market_emulator.fragment_generator import FragmentGenerator
import logging

class FragmentGeneratorIndex (unittest.TestCase):
    def setUp (self):
        self.frag_gen = FragmentGenerator ('BTC_ETH', '../fragments/')
        self.frag_gen.keep_frags_in_mem = True
        self.frag_gen.force_overwrite_frags = True
        self.frag_gen.extend_from_raw_dirs(['../data/1530224636/'])

    def test_monotonicity (self):   # This is a stupid test, as SortedDict is defined as strong monotonous.
        f = self.frag_gen.frags[1]
        price = 0
        for p in f.asks_ob.keys():
            self.assertGreater (p, price)
            price = p
        price = 1000000000000
        for p in f.bids_ob.__reversed__():
            self.assertLess (p, price)
            price = p

if __name__ == '__main__':
    unittest.main()
