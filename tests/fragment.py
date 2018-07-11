import unittest
import importlib
#importlib.import('../market_emulator/fragment.py')
#__import__('../market_emulator/fragment.py')
import sys
import os
#sys.path.append(os.path.abspath("../market_emulator"))
sys.path.append(os.path.abspath(".."))
from market_emulator.fragment import Fragment, FragmentGenerator
import logging
import json

class FragmentGeneratorTestCase(unittest.TestCase):
    def setUp(self):
        self.frag_gen = FragmentGenerator ('BTC_ETH', '../fragments/')

    def test_extend (self):
        self.frag_gen.keep_frags_in_mem = True
        self.frag_gen.extend_from_raw_dirs(['../data/1530224636/'])

"""
class FragmentTestCase(unittest.TestCase):
    def setUp(self):
        test_fn = '../data/1530224636/BTC_ETH'
        print('loading test file ' + test_fn)
        self.fragment = Fragment('../data/1530224636/BTC_ETH');
        print('done.')

    def test_readlines (self):
        self.assertEqual(1, 1, msg='{0}'.format(self.fragment.raw_ob))
        logging.debug("Length of raw_ob: " + str(len(json.dumps(self.fragment.raw_ob))) + " chars")
        logging.debug("Length of first update: " + str(len(json.dumps(self.fragment.raw_updates[0]))) + " chars")
        logging.debug("Length of last update: " + str(len(json.dumps(self.fragment.raw_updates[-1]))) + " chars")
        self.assertNotEqual(len(json.dumps(self.fragment.raw_updates[0])),
                            len(json.dumps(self.fragment.raw_ob)), msg='First update seems to be the raw ob')

    def test_timerange (self):
        range = self.fragment.end - self.fragment.start
        logging.error('fragment spans ' + str(range) + 'ms')
        self.assertGreater(range, 0, msg='Fragment spans non-positive time range')
"""    
if __name__ == '__main__':
    unittest.main()
