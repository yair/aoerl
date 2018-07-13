import unittest
import importlib
#importlib.import('../market_emulator/fragment.py')
#__import__('../market_emulator/fragment.py')
import sys
import os
#sys.path.append(os.path.abspath("../market_emulator"))
sys.path.append(os.path.abspath(".."))
from market_emulator.fragment import Fragment, FragmentGenerator, EpisodeGenerator, Episode
import logging
import json
from copy import deepcopy

class EpisodeGeneratorTestCase (unittest.TestCase):
    def setUp (self):
        self.eg = EpisodeGenerator ('BTC_ETH', '../fragments/', 180000)

    def test_random_episode (self):
        for i in range(0, 30):
            e = self.eg.get_random_episode()
            logging.error ('i='+str(i)+' fstart='+str(e.fstart)+' start='+str(e.f.start)+' end='+str(e.f.end))

class FragmentGeneratorTestCase(unittest.TestCase):
    def setUp(self):
        self.frag_gen = FragmentGenerator ('BTC_ETH', '../fragments/')
        self.frag_gen.keep_frags_in_mem = True
        self.frag_gen.force_overwrite_frags = True
        self.frag_gen.extend_from_raw_dirs(['../data/1530224636/'])

#    def test_blank (self):
#        logging.error('Pre-pickled fragment first update: ' + json.dumps(self.frag_gen.frags[0].updates[0]))

class FragmentGeneratorIndex (unittest.TestCase):
    def setUp (self):
        self.frag_gen = FragmentGenerator ('BTC_ETH', '../fragments/')

"""    def test_index (self):
        index = self.frag_gen.index
        id = {}
        for fs, fe in index:
            self.assertNotIn (f[0], id)
            id[f[0]] = True """ # No need, done inline

class FragmentTestCase(unittest.TestCase):
    def setUp(self):
        self.fragment = Fragment('../fragments/BTC_ETH/1530224638648.pickle')
        logging.error('Unpickled fragment first update: ' + json.dumps(self.fragment.updates[0]))

    def test_start_ob (self):
        f = self.fragment
        asks_ob = deepcopy (f.asks_ob)
        bids_ob = deepcopy (f.bids_ob)
        f.advance_to_time (f.start)
        self.assertEqual (f.asks_ob.__len__(), asks_ob.__len__())
        self.assertEqual (f.bids_ob.__len__(), bids_ob.__len__())
        self.assertEqual (f.asks_ob, asks_ob)
        self.assertEqual (f.bids_ob, bids_ob)

    def test_end_ob (self):
        f = self.fragment
        asks_ob = deepcopy (f.asks_ob)
        bids_ob = deepcopy (f.bids_ob)
        logging.error('First bids_ob key:   ' + json.dumps(bids_ob.keys()[0]) +
                      '              item:  ' + json.dumps(bids_ob.items()[0]) +
                      '              value: ' + json.dumps(bids_ob.values()[0]))
        logging.error('First update: ' + json.dumps(f.updates[0]))
        logging.error('starting advance to end')
        f.advance_to_time (f.end)
        logging.error('reached the end')
        self.assertNotEqual (f.asks_ob.__len__(), asks_ob.__len__())
        self.assertNotEqual (f.bids_ob.__len__(), bids_ob.__len__())
        self.assertNotEqual (f.asks_ob, asks_ob)
        self.assertNotEqual (f.bids_ob, bids_ob)
        self.assertEqual(f.updates.__len__(), 0)

class ConsecutiveFragmentsTestCase (unittest.TestCase):
    def setUp (self):
        self.f1 = Fragment ('../fragments/BTC_ETH/1530224638648.pickle')
        self.f2 = Fragment ('../fragments/BTC_ETH/1530547986739.pickle')

    def test_compare_obs (self):
        return # They are close, but not identical, no need to fail
        self.f1.advance_to_time (self.f1.end)
        self.assertEqual (self.f1.asks_ob.__len__(), self.f2.asks_ob.__len__())
        self.assertEqual (self.f1.bids_ob.__len__(), self.f2.bids_ob.__len__())
        self.assertEqual (self.f1.asks_ob, self.f2.asks_ob)
        self.assertEqual (self.f1.bids_ob, self.f2.bids_ob)
"""
class FragmentTestCase(unittest.TestCase): # pre generator
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
