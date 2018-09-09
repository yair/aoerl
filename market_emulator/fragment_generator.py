from __future__ import absolute_import, division, print_function

import json
import logging
from sortedcontainers import SortedDict
import pickle
import os
import fnmatch
import glob
from os.path import isfile, join

from market_emulator.fragment import *
#from market_emulator.reverse_fragment import ReverseFragment
from market_emulator.fragment_index import FragmentIndex

class FragmentGenerator:    # TODO: Fragmentize further, to reduce seek time (after 1 day, let's say, although can be smaller if we can use two consecutive frags in the
                            #       same episode
                            # TODO: Break up class into generator, index and episode manager, also to different files

    def __init__ (self, market, basefragdir):
        self.market = market
        self.fragdir = basefragdir + market + "/"
        if not os.path.exists(self.fragdir):
            os.makedirs(self.fragdir)
            logging.error("created non-existent " + self.fragdir)
        self.frags = []
        self.keep_frags_in_mem = False
        self.force_overwrite_frags = False
#        self.index_fn = self.fragdir + "index.json"
        # Load index from fragdir
#        self.index = FragmentIndex (market, basefragdir)
#        if not self.index.loaded:
#            self.reindex ()

    def reindex (self):
        return # crashes and we don't use it
        for fn in os.listdir(self.fragdir):
            if fnmatch.fnmatch(fn, '*.pickle'):
                f = Fragment (self.fragdir + fn)
                assert str(f.start) + '.pickle' == fn
                self.index.add_frag (f)
        self.index.save()

    def extend_from_raw_dirs (self, raw_dirs):
        for raw_dir in raw_dirs:
            logging.error("extending " + self.market + " from " + raw_dir);
            self.parse_raw_file(join(raw_dir, self.market))

    def parse_raw_file (self, raw_file):    # Raw files are as-is exchange stream recordings, one line per event
        if not os.path.exists(raw_file):
            return
        with open (raw_file, 'r') as fh:
            lines = fh.readlines()      # This might bite us if files are too large
        try:
            lines = [json.loads(x) for x in lines]
        except:
            logging.error("Malformed json file: " + raw_file)
            return
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
                if fragment != None and len(fragment.updates) > 0:
                    fragment.end = fragment.updates[-1][0]
                    self.store_fragment (fragment)
#                    self.index.add_frag (fragment)  # What about the index? And do we want to keep it in memory (yes, but just for consec fragment sanity check)
#                    rv = ReverseFragment (None)
#                    rv.init_from_fragment (fragment)
#                    self.store_reversed_fragment (rv)

                fragment = Fragment()
                if len(line['payload'][0]['data']['asks']) < 1 or len(line['payload'][0]['data']['bids']) < 1:
                    return # malformed ob
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
        if len(fragment.updates) > 0:
            fragment.end = fragment.updates[-1][U_TIME]
            self.store_fragment (fragment)
#        self.index.add_frag (fragment)
#        rv = ReverseFragment (None)
#        rv.init_from_fragment (fragment)
#        self.store_reversed_fragment (rv)

    def init_sorted_dict (self, d): # TODO: Diff bids from asks (the latter should be reversed)
        ret = SortedDict()
        for key, value in d.items():
            ret.update ({int(round(float(key) * REZ)) : int(round(float(value) * REZ))})
        return ret

    def store_fragment (self, fragment):
        if self.keep_frags_in_mem:
            self.frags.append(fragment)
        pickle_fn = self.fragdir + str(fragment.start) + ".pickle"
#        if not os.path.exists(self.fragdir):
#            os.makedirs(self.fragdir)
        if os.path.exists(pickle_fn):
            if self.force_overwrite_frags:
                logging.error("Forcing over-writing of " + pickle_fn)
            else:
                logging.error("Not forcing over-writing of " + pickle_fn)
                return
        with open (pickle_fn, 'wb') as fh:
            pickle.dump (fragment, fh)

#    def store_reversed_fragment (self, rv):
#        pickle_fn = self.fragdir + str(rv.start) + "_reversed.pickle"
#        with open (pickle_fn, 'wb') as fh:
#            pickle.dump (rv, fh)
        
if __name__ == '__main__':
    fragdir = '../fragments/'
    rawdirs = glob.glob('../data/*')
    markets = ['BTC_AMP', 'BTC_ARDR', 'BTC_BCH', 'BTC_BCN', 'BTC_BCY', 'BTC_BLK', 'BTC_BTCD', 'BTC_BTM', 'BTC_BTS', 'BTC_BURST', 'BTC_CLAM', 'BTC_CVC', 'BTC_DASH', 'BTC_DCR', 'BTC_DGB', 'BTC_DOGE', 'BTC_EMC2', 'BTC_ETC', 'BTC_ETH', 'BTC_EXP', 'BTC_FCT', 'BTC_FLDC', 'BTC_FLO', 'BTC_GAME', 'BTC_GAS', 'BTC_GNO', 'BTC_GNT', 'BTC_GRC', 'BTC_HUC', 'BTC_LBC', 'BTC_LSK', 'BTC_LTC', 'BTC_MAID', 'BTC_NAV', 'BTC_NEOS', 'BTC_NMC', 'BTC_NXC', 'BTC_NXT', 'BTC_OMG', 'BTC_OMNI', 'BTC_PASC', 'BTC_PINK', 'BTC_POT', 'BTC_PPC', 'BTC_RADS', 'BTC_REP', 'BTC_RIC', 'BTC_SBD', 'BTC_SC', 'BTC_STEEM', 'BTC_STORJ', 'BTC_STR', 'BTC_STRAT', 'BTC_SYS', 'BTC_VIA', 'BTC_VRC', 'BTC_VTC', 'BTC_XBC', 'BTC_XCP', 'BTC_XEM', 'BTC_XMR', 'BTC_XPM', 'BTC_XRP', 'BTC_XVC', 'BTC_ZEC', 'BTC_ZRX', 'USDT_BTC']
#    markets = ['BTC_AMP']
    for m in markets:
        FragmentGenerator (m, fragdir).extend_from_raw_dirs(rawdirs)
