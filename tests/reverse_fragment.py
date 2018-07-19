import unittest
import importlib
import sys
import os
sys.path.append(os.path.abspath(".."))
import logging
import json
from copy import deepcopy

from market_emulator.fragment import *
from market_emulator.reverse_fragment import ReverseFragment

class FragmentTestCase(unittest.TestCase):
    def setUp(self):
        logging.error('setUp')

    def test_init_from_f (self):
        f = Fragment('../fragments/BTC_ETH/1530224638648.pickle')
#        logging.error('Unpickled fragment first update: ' + json.dumps(self.fragment.updates[0]))
        r_f = ReverseFragment ()
        r_f.init_from_fragment (f)

    def test_double_inversion (self):
        f = Fragment('../fragments/BTC_ETH/1530224638648.pickle')
#        logging.error('Unpickled fragment first update: ' + json.dumps(self.fragment.updates[0]))
        r_f = ReverseFragment ()
        r_f.init_from_fragment (f)
        r_f2 = ReverseFragment ()
        r_f2.init_from_fragment (r_f)
        self.assertNotEqual (f.asks_ob.__len__(), r_f2.asks_ob.__len__())
        self.assertNotEqual (f.bids_ob.__len__(), r_f2.bids_ob.__len__())
        self.assertNotEqual (f.asks_ob, r_f2.asks_ob)
        self.assertNotEqual (f.bids_ob, r_f2.bids_ob)

if __name__ == '__main__':
    unittest.main()
