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
        # Load index from fragdir

    def extend_from_raw_dirs (self, raw_dirs):
        self.frags = []
        for raw_dir in raw_dirs:
            self.frags.extend(self.parse_raw_file(raw_dir + market)

class Fragment:
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
        
        
