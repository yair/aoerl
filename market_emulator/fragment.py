from __future__ import absolute_import, division, print_function

#import numpy as np
#import pandas as pd
import json
import logging
from sortedcontainers import SortedDict #, SortedList
#from sortedcontainers import SortedKeyList
from enum import Enum
import pickle
import os
from collections import deque

#class UpType (Enum):
MODIFY = 0
REMOVE = 1
NEW_TRADE = 2

#class OrType (Enum):
ASK = 0
BID = 1
BUY = 2
SELL = 3

REZ = 100000000

class FragmentGenerator:    # TODO: Fragmentize further, to reduce seek time (after 1 day, let's say, although can be smaller if we can use two consecutive frags in the
                            #       same episode

    def __init__ (self, market, basefragdir):
        self.market = market
        self.fragdir = basefragdir + market + "/"
        self.frags = []
        self.keep_frags_in_mem = False
        self.force_overwrite_frags = False
        self.index_fn = self.fragdir + "index.json"
        # Load index from fragdir
        if os.path.exists(self.index_fn):
            with open (self.index_fn, 'r') as fh:
                self.index = json.load (fh)
        else:
            self.index = []

    def extend_from_raw_dirs (self, raw_dirs):
        for raw_dir in raw_dirs:
            logging.error("extending from " + raw_dir);
#            self.frags.extend(self.parse_raw_file(raw_dir + self.market))
            self.parse_raw_file(raw_dir + self.market)

    def parse_raw_file (self, raw_file):
        with open (raw_file, 'r') as fh:
            lines = fh.readlines()      # This might bite us if files are too large
        lines = [json.loads(x) for x in lines]
        fragment = None
        i = 0
        time = 0
        uid = 0
        for line in lines:
            if line['payload'][0]['type'] == 'orderBook':
                if i == 0:
                    assert fragment == None
                else:
                    assert fragment != None
                if fragment != None:
                    fragment.end = fragment.updates[-1][0]
                    self.store_fragment (fragment)
                    self.add_to_index (fragment)  # What about the index? And do we want to keep it in memory (yes, but just for consec fragment sanity check)

                fragment = Fragment()
                fragment.asks_ob = self.init_sorted_dict (line['payload'][0]['data']['asks'])
                fragment.bids_ob = self.init_sorted_dict (line['payload'][0]['data']['bids'])
#                fragment.asks_ob = SortedDict (line['payload'][0]['data']['asks'])
#                fragment.bids_ob = SortedDict (line['payload'][0]['data']['bids'])
                fragment.start = line['time']
#                fragment.seq = line['seq']
            else:
                assert fragment != None
                if line['time'] != time:
                    uid = 0
                time = line['time']
#                seq = line['seq']
                for u in line['payload']:
                    if u['type'] == 'orderBookModify':
                        up_type = MODIFY
                    elif u['type'] == 'orderBookRemove':
                        up_type = REMOVE
                    elif u['type'] == 'newTrade':
                        up_type = NEW_TRADE
                    else:
                        assert False, "u['type'] = " + u['type']
#                    up_type = UpType.MODIFY if u['type'] == 'orderBookModify' else UpType.REMOVE if u['type'] == 'orderBookRemove' else assert False
#                    or_type = OrType.ASK if u['date']['type'] == 'ask' else: OrType.BID if u['data']['type'] == 'bid' else: assert False
                    if u['data']['type'] == 'ask':
                        or_type = ASK
                    elif u['data']['type'] == 'bid':
                        or_type = BID
                    elif u['data']['type'] == 'buy':
                        or_type = BUY
                    elif u['data']['type'] == 'sell':
                        or_type = SELL
                    else:
                        assert False, "u['data']['type'] = " + u['data']['type']
#                    rate = float(u['data']['rate']) # Can we integerify these two? Do we know they always have 8 decimals in all markets?
#                    amount = float(u['data']['amount'])
#                    rate = str(u['data']['rate']) # Can we integerify these two? Do we know they always have 8 decimals in all markets?
#                    amount = str(u['data']['amount'])
                    rate = int(round(float(u['data']['rate']) * REZ))
                    amount = int(round(float(u['data']['amount']) * REZ))
                    assert uid != 998
                    fragment.updates.append((time, uid, up_type, or_type, rate, amount))
#                    fragment.updates.add((time, uid, up_type, or_type, rate, amount))
                    uid = uid + 1
                    if i == 13:
                        logging.error(fragment.updates[-1])
                        logging.error(json.dumps(fragment.updates[-1]))
#            orderBook - if first, just init fragment. If not, pickle and index the old one, then init.
            i = i + 1
        fragment.end = fragment.updates[-1][0]
        self.store_fragment (fragment)
        self.add_to_index (fragment)  # What about the index? And do we want to keep it in memory (yes, but just for consec fragment sanity check)
#        pickle and index the orderbook and its updates
#        Find a way, on multiple obs i the same raw file, to run the first to the end and compare to the second.

    def init_sorted_dict (self, d):
        ret = SortedDict()
        for key, value in d.items():
            ret.update ({int(round(float(key) * REZ)) : int(round(float(value) * REZ))})
        return ret

    def store_fragment (self, fragment):
        if self.keep_frags_in_mem:
            self.frags.append(fragment)
        pickle_fn = self.fragdir + str(fragment.start) + ".pickle"
        if not os.path.exists(self.fragdir):
            os.makedirs(self.fragdir)
        if os.path.exists(pickle_fn):
            if self.force_overwrite_frags:
                logging.error("Forcing over-writing of " + pickle_fn)
            else:
                logging.error("Not forcing over-writing of " + pickle_fn)
                return
        with open (pickle_fn, 'wb') as fh:
            pickle.dump (fragment, fh)

    def add_to_index (self, fragment):
        self.index.append((fragment.start, fragment.end))
        with open (self.index_fn, 'w') as fh:
            json.dump (self.index, fh)

class Fragment:
    def __init__ (self, pickle_fn = None):
        if (pickle_fn != None):
            self.load_from_pickle (pickle_fn)
        else:
            self.reset()

    def reset(self):
        self.asks_ob = None
        self.bids_ob = None
        self.start = None
        self.end = None
#        self.updates = []
#        self.updates = SortedKeyList(key = lambda update: "%d%03d" % (update[0], update[1]))
#        self.updates = SortedList(key = lambda update: "%d%03d" % (update[0], update[1]))   # Why? We never update and only read sequentially.
        self.updates = deque()

    def load_from_pickle (self, pickle_fn):
        with open (pickle_fn, 'rb') as fh:
            tmpfrag = pickle.load(fh)
            self.asks_ob = tmpfrag.asks_ob
            self.bids_ob = tmpfrag.bids_ob
            self.start = tmpfrag.start
            self.end = tmpfrag.end
            self.updates = deque (tmpfrag.updates)

    def advance_to_time(self, time):
        logging.error("Advancing from " + str(self.start) + " to " + str(time))
        self.removes = 0
        self.modifies = 0
        while self.updates.__len__() > 0 and self.updates[0][0] <= time:
            self.single_step()
        logging.error('Advancing done after ' + str(self.removes) + ' removes and ' + str(self.modifies) + ' modifications')

    def get_slice(self, time, duration):  # both in ms
        pass

    def single_step (self): # Really? How do we check collisions like that?
#        u = self.updates.popitem(0)
        u = self.updates.popleft()
#        logging.error("single step: " + str(self.start) + " => " + str(u[0]));
        self.start = u[0]
        ob = None
#                    fragment.updates.add((time, uid, up_type, or_type, rate, amount))
        if u[2] == NEW_TRADE:
            return
        if u[3] == ASK:
            ob = self.asks_ob
        elif u[3] == BID:
            ob = self.bids_ob
        else:
            assert False, "u = " + str(u)
        if u[2] == REMOVE:
#            if (u[4] in ob):
#                logging.error('removing (existing) order at ' + str(u[4]))
            assert u[4] in ob, 'About to remove ' + str(u[4]) + ' from ob, but it is not there'
#            ob.popitem(u[4])
            ob.pop(u[4])
            assert u[4] not in ob, 'Order at ' + str(u[4]) + ' still in ob after removal'
            self.removes = self.removes + 1
        elif u[2] == MODIFY:
            ob.update({u[4]: u[5]})
            assert u[4] in ob, 'Order at ' + str(u[4]) + ' not in ob after modification'
            self.modifies = self.modifies + 1
        else:
            assert False

    def get_ob (self, time):
        if (time < self.start or time > self.end):
            logging.error("get_ob: time given (" + time + ") outside of fragment range [" + self.start + ", " + self.end + "]")
            assert False
            return [];

        last_update = self.find_last_update (time) # TODO: test on time=start, time=end
        return run_to_update(last_update)

    def find_last_update (self, time):
        pass
#        bisecting this, how?
"""
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
"""



        
        
