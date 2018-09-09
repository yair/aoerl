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

class BinanceFragmentGenerator:

    def __init__ (self, market, basefragdir):
        self.market = market
        self.fragdir = basefragdir + market + "/"
        if not os.path.exists(self.fragdir):
            os.makedirs(self.fragdir)
            logging.error("created non-existent " + self.fragdir)
        self.frags = []
        self.keep_frags_in_mem = False
        self.force_overwrite_frags = False

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
            logging.error("extending from " + raw_dir);
            self.parse_raw_file(join(raw_dir, self.market))

    def parse_raw_file (self, raw_file):    # Raw files are as-is exchange stream recordings, one line per event
        if not os.path.exists(raw_file):
            return
        with open (raw_file, 'r') as fh:
            lines = fh.readlines()      # This might bite us if files are too large
        lines = [json.loads(x) for x in lines]
        fragment = None
        i = 0
        time = 0
        uid = 0
        for line in lines:
#            if line['payload'][0]['type'] == 'orderBook':
            if 'lastUpdateId' in line.keys():   # obs
                if i == 0:
                    assert fragment == None, 'OB in the middle of stream? i=' + str(i) + ' raw_file=' + raw_file
                else:
#                    assert False # fragment != None # Only one ob per file in binance
                    assert fragment != None # Now multiple ones
                if fragment != None and len(fragment.updates) > 0:
#                    fragment.end = fragment.updates[-1][0]
                    self.store_fragment (fragment)

                fragment = Fragment()
                fragment.asks_ob = self.init_sorted_dict (line['asks'])
                fragment.bids_ob = self.init_sorted_dict (line['bids'])
#                fragment.asks_ob = self.init_sorted_dict (line['payload'][0]['data']['asks'])
#                fragment.bids_ob = self.init_sorted_dict (line['payload'][0]['data']['bids'])
#                fragment.start = line['time']      # TODO: take it from the first update
            else:
                if fragment == None:
                    logging.error('BROKEN FILE ' + raw_file + '. Aborting.')
                    return
                assert fragment != None, 'Update to non-existant OB? i=' + str(i) + ' raw_file=' + raw_file
# {"e":"trade","E":1532949470799,"s":"ADABTC","t":16545885,"p":"0.00001951","q":"629.00000000","b":48174832,"a":48174834,"T":1532949470797,"m":true,"M":true}
#  "e": "trade",     // Event type
#  "E": 123456789,   // Event time
#  "s": "BNBBTC",    // Symbol
#  "t": 12345,       // Trade ID
#  "p": "0.001",     // Price
#  "q": "100",       // Quantity
#  "b": 88,          // Buyer order ID
#  "a": 50,          // Seller order ID
#  "T": 123456785,   // Trade time
#  "m": true,        // Is the buyer the market maker?
#  "M": true         // Ignore
                if line['e'] == 'trade':    # Trades are always one per line
                    if line['m']:
                        or_type = ORT_SELL
                    else:
                        or_type = ORT_BUY
                    fragment.updates.append((line['T'], line['t'], UPT_NEW_TRADE, or_type, int(round(float(line['p'])*REZ)), int(round(float(line['q'])*REZ))))
# {"e":"depthUpdate","E":1532949473542,"s":"ADABTC","U":76816534,"u":76816536,"b":[["0.00001951","0.00000000",[]],["0.00001945","15129.00000000",[]],["0.00001937","12431.00000000",[]]],"a":[["0.00001951","942.00000000",[]]]}
                elif line['e'] == 'depthUpdate':
                    uid = line['U']
                    for u in line['b']: #bids
                        if int (float (u[1]) * REZ) == 0:
                            up_type = UPT_REMOVE
                        else:
                            up_type = UPT_MODIFY
                        fragment.updates.append((line['E'], uid, up_type, ORT_BID, int(round(float(u[0])*REZ)), int(round(float(u[1])*REZ))))
                        uid = uid + 1
                    for u in line['a']: #asks
                        if int (float (u[1]) * REZ) == 0:
                            up_type = UPT_REMOVE
                        else:
                            up_type = UPT_MODIFY
                        fragment.updates.append((line['E'], uid, up_type, ORT_ASK, int(round(float(u[0])*REZ)), int(round(float(u[1])*REZ))))
                        uid = uid + 1
                else:
                    assert False, "Unknown update type: " + line['e']
                """
#                if line['time'] != time:
#                    uid = 0
#                time = line['time']
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
                """
            i = i + 1
#        fragment.start = fragment.updates[0][U_TIME]
#        fragment.end = fragment.updates[-1][U_TIME]
        self.store_fragment (fragment)

    def init_sorted_dict (self, d): # TODO: Diff bids from asks (the latter should be reversed)
        ret = SortedDict()
        for key, value in d.items():
            ret.update ({int(round(float(key) * REZ)) : int(round(float(value) * REZ))})
        return ret

    def store_fragment (self, fragment):
        fragment.start = fragment.updates[0][U_TIME]
        fragment.end = fragment.updates[-1][U_TIME]
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

if __name__ == '__main__':
    fragdir = '../binance_fragments/'
#    rawdirs = glob.glob('../binance_data/*')
    rawdirs = ['../binance_data/1533533058']
    markets = []
    if markets == []:
        mhash = {}
        for rawdir in rawdirs:
            mdirs = glob.glob(rawdir + '/*')
#            logging.error('mdirs: ' + str(mdirs))
            for mdir in mdirs:
                mhash[os.path.basename(mdir)] = True
        markets = mhash.keys()
#    logging.error('markets: ' + str(markets))
    for m in markets:
        BinanceFragmentGenerator (m, fragdir).extend_from_raw_dirs(rawdirs)
