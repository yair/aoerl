from __future__ import absolute_import, division, print_function

import json
import logging
from sortedcontainers import SortedDict
import pickle
import os
import fnmatch

from market_emulator.fragment import Fragment

class FragmentGenerator:    # TODO: Fragmentize further, to reduce seek time (after 1 day, let's say, although can be smaller if we can use two consecutive frags in the
                            #       same episode
                            # TODO: Break up class into generator, index and episode manager, also to different files

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
            self.reindex ()

    def reindex (self):
        self.index = {}
        for fn in os.listdir(self.fragdir):
            if fnmatch.fnmatch(fn, '*.pickle'):
                f = Fragment (self.fragdir + fn)
                assert str(f.start) + '.pickle' == fn
                self.add_to_index (f)
        self.save_index()

    def save_index (self):
        with open (self.index_fn, 'w') as fh:
            json.dump (self.index, fh)

    def extend_from_raw_dirs (self, raw_dirs):
        for raw_dir in raw_dirs:
            logging.error("extending from " + raw_dir);
            self.parse_raw_file(raw_dir + self.market)

    def parse_raw_file (self, raw_file):    # Raw files are as-is exchange stream recordings, one line per event
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
                fragment.start = line['time']
            else:
                assert fragment != None
                if line['time'] != time:
                    uid = 0
                time = line['time']
                for u in line['payload']:
                    if u['type'] == 'orderBookModify':
                        up_type = UPT_MODIFY
                    elif u['type'] == 'orderBookRemove':
                        up_type = UPT_REMOVE
                    elif u['type'] == 'newTrade':
                        up_type = UPT_NEW_TRADE
                    else:
                        assert False, "u['type'] = " + u['type']
                    if u['data']['type'] == 'ask':
                        or_type = ORT_ASK
                    elif u['data']['type'] == 'bid':
                        or_type = ORT_BID
                    elif u['data']['type'] == 'buy':
                        or_type = ORT_BUY
                    elif u['data']['type'] == 'sell':
                        or_type = ORT_SELL
                    else:
                        assert False, "u['data']['type'] = " + u['data']['type']
                    rate = int(round(float(u['data']['rate']) * REZ))
                    amount = int(round(float(u['data']['amount']) * REZ))
                    assert uid != 998
                    fragment.updates.append((time, uid, up_type, or_type, rate, amount))
                    uid = uid + 1
                    if i == 13:
                        logging.error(fragment.updates[-1])
                        logging.error(json.dumps(fragment.updates[-1]))
            i = i + 1
        fragment.end = fragment.updates[-1][U_TIME]
        self.store_fragment (fragment)
        self.add_to_index (fragment)

    def init_sorted_dict (self, d): # TODO: Diff bids from asks (the latter should be reversed)
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

    def add_to_index (self, f):
        assert f.start not in self.index
        self.index[f.start] = f.end