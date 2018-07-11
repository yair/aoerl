from __future__ import absolute_import, division, print_function

#import numpy as np
#import pandas as pd
import json
import logging
from sortedcontainers import SortedDict, SortedList
from enum import Enum

class UpType (Enum):
    MODIFY = 0
    REMOVE = 1
    NEW_TRADE = 2

class OrType (Enum):
    ASK = 0
    BID = 1
    BUY = 2
    SELL = 3

class FragmentGenerator:
    def __init__ (self, market, fragdir):
        self.market = market
        self.fragdir = fragdir
        self.frags = []
        # Load index from fragdir

    def extend_from_raw_dirs (self, raw_dirs):
        for raw_dir in raw_dirs:
            self.frags.extend(self.parse_raw_file(raw_dir + market))

    def parse_raw_file (self, raw_file):
        with open (raw_file, 'r') as fh:
            lines = fh.readlines()      # This might bite us if files are too large
        lines = [json.loads(x) for x in lines]
        fragment = None
        i = 0
        for line in lines:
            if line['payload']['type'] == 'orderBook':
                if i == 0:
                    assert fragment == None
                else
                    assert fragment != None
                if (fragment != None)
                    store_fragment (fragment)
                    add_to_index (fragment)  # What about the index? And do we want to keep it in memory (yes, but just for consec fragment sanity check)

                fragment = Fragment()
                fragment.asks_ob = SortedDict (self.raw_ob['payload'][0]['data']['asks'])
                fragment.bids_ob = SortedDict (self.raw_ob['payload'][0]['data']['bids'])
                fragment.start = line['time']
#                fragment.seq = line['seq']
            else:
                assert fragment != None
                time = line['time']
#                seq = line['seq']
                for u in line['payload']:
                    if u['type'] == 'orderBookModify':
                        up_type = UpType.MODIFY
                    elif u['type'] == 'orderBookRemove':
                        up_type = UpType.REMOVE
                    elif u['type'] == 'newTrade':
                        up_type = UpType.NEW_TRADE
                    else:
                        assert False, "u['type'] = " + u['type']
#                    up_type = UpType.MODIFY if u['type'] == 'orderBookModify' else UpType.REMOVE if u['type'] == 'orderBookRemove' else assert False
#                    or_type = OrType.ASK if u['date']['type'] == 'ask' else: OrType.BID if u['data']['type'] == 'bid' else: assert False
                    if u['data']['type'] == 'ask':
                        or_type = OrType.ASK
                    elif u['data']['type'] == 'bid':
                        or_type = OrType.BID
                    elif u['data']['type'] == 'buy':
                        or_type = OrType.BUY
                    elif u['data']['type'] == 'sell':
                        or_type = OrType.SELL
                    else:
                        assert False, "u['data']['type'] = " + u['data']['type']
                    rate = float(u['data']['rate']) # Can we integerify these two? Do we know they always have 8 decimals in all markets?
                    amount = float(u['data']['amount'])
                    fragment.updates.append((time, up_type, or_type, rate, amount))
                    if i == 13:
                        logging.error(fragment.updates[-1])




                fragment.updates.append


            orderBook - if first, just init fragment. If not, pickle and index the old one, then init.
            i = i + 1
        pickle and index the orderbook and its updates
        Find a way, on multiple obs i the same raw file, to run the first to the end and compare to the second.

    def store_fragment (self, fragment):
        pass




class Fragment:
    def __init__ (self, pickle_fn = None):
        self.asks_ob = None
        self.bids_ob = None
        self.start = None
        self.end = None
        self.updates = []

        if (pickle_fn != None):
            self.load_from_pickle (pickle_fn)

    def load_from_pickle (self, pickle_fn):
        pass

    def save_to_pickle (self, pickle_fn):
        pass

    def __init__ (self, fn): # Why does this func takes 23s regardless of file size? Also, more than one frag can be stored in a raw file.

        self.raw_fn = fn


        with open(fn, 'r') as fh:
            self.raw_ob = json.loads(fh.readline())
            self.asks_ob = SortedDict (self.raw_ob['payload'][0]['data']['asks'])
            logging.error("Got " + str(self.asks_ob.__len__()) + " asks.")
            self.bids_ob = SortedDict (self.raw_ob['payload'][0]['data']['bids'])
            logging.error("Got " + str(self.bids_ob.__len__()) + " bids.")
            logging.error('ob loaded')
            logging.debug(self.raw_ob)
            self.start = self.raw_ob['time']
            self.raw_updates = fh.readlines()
            logging.error('updates read')
            self.raw_updates = [json.loads(x) for x in self.raw_updates]
            self.end = self.raw_updates[-1]['time']
            logging.error('updates dejsonified')
            for update in self.raw_updates:
                time = update['time']
                seq = update['seq']
                for u in update['payload']:
                    if u['type'] == 'orderBookModify':
                        up_type = UpType.MODIFY
                    elif u['type'] == 'orderBookRemove':
                        up_type = UpType.REMOVE
                    elif u['type'] == 'newTrade':
                        up_type = UpType.NEW_TRADE
                    else:
                        assert False, "u['type'] = " + u['type']
#                    up_type = UpType.MODIFY if u['type'] == 'orderBookModify' else UpType.REMOVE if u['type'] == 'orderBookRemove' else assert False
#                    or_type = OrType.ASK if u['date']['type'] == 'ask' else: OrType.BID if u['data']['type'] == 'bid' else: assert False
                    if u['data']['type'] == 'ask':
                        or_type = OrType.ASK
                    elif u['data']['type'] == 'bid':
                        or_type = OrType.BID
                    elif u['data']['type'] == 'buy':
                        or_type = OrType.BUY
                    elif u['data']['type'] == 'sell':
                        or_type = OrType.SELL
                    else:
                        assert False, "u['data']['type'] = " + u['data']['type']
                    rate = float(u['data']['rate'])
                    amount = float(u['data']['amount'])
            logging.error('updates atomized')




    def get_ob (self, time):
        if (time < self.start or time > self.end):
            logging.error("get_ob: time given (" + time + ") outside of fragment range [" + self.start + ", " + self.end + "]")
            return [];
        
        
