from os import listdir
from os.path import isfile, join
from fnmatch import fnmatch
from copy import deepcopy
import itertools
import time

import numpy as np
import math

from market_emulator.fragment import *
from market_emulator.reverse_fragment import ReverseFragment

ACTIONS = 8

# Action LookUp
ALU_1AV      = 0
ALU_05AV     = 1
ALU_025AV    = 2
ALU_0125AV   = 3
ALU_00625AV  = 4
ALU_NEAR     = 5
ALU_MID      = 6
ALU_FAR      = 7

# Mode LookUp # TODO: move to episode, and have a third option of random
MLU_BUY = 0
MLU_SELL = 1

PRICE_RESOLUTION = 1    # satoshi (whatabout BTC_USD?)


class RLExec:
    def __init__ (self, basefragdir, market, period, time_rez, volume, vol_rez, average_vol):
        self.period = period        # in ms
        self.time_rez = time_rez    # number of time intervals
        self.volume = volume        # in satoshi
        self.vol_rez = vol_rez      # number of volume intervals
        self.fragdir = join (basefragdir, market)
#        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*reversed.pickle')])
        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*1530547986739_reversed.pickle')])
        self.q = np.zeros((2, time_rez, vol_rez, ACTIONS), dtype=float)
        self.elen = float(self.period) / self.time_rez
        self.gen = 0. # Global Episode Number, for normalization
        self.average_volume = average_vol

    def train_all (self):
        for i in range(self.time_rez - 1, -1, -1):
            logging.error('===================================================')
            logging.error('Now calculating optimal action for time step ' + str(i+1) + '/' + str(self.time_rez))
            logging.error('===================================================')
            for fn in self.frag_fns:
                self.train_fragment (i, ReverseFragment (fn))
            logging.error(str(self.q))

    def train_fragment (self, i, rf):
        episodes = int(math.floor((rf.end - rf.start) / self.elen))
        logging.error('This fragment contains ' + str(episodes) + ' episodes of ' + str(self.elen) + 'ms')
        # TODO: Drop first episode
        for e in range (episodes - 1, -1, -1):
            a = time.time()
            (rf, oe) = self.get_episode (rf, e)
            oe.mo_cost = market_order_cost (oe)
            b = time.time()
            self.train_episode (i, oe, MLU_BUY)
            c = time.time()
            logging.error('fetching episode took ' + str (b-a) + 's. Training took ' + str (c-b) + 's')
#            self.train_episode (i, oe, MLU_SELL)

    def get_episode (self, rf, e):
        x = 0
        oe = ReverseFragment (None)
        oe.start = rf.start + e * self.elen
        oe.end = rf.start + (e + 1) * self.elen
#        rf.updates = deque (itertools.islice (rf.updates, fro, to)...
        while rf.updates[0][U_TIME] > oe.end:
            rf.updates.popleft ()
            x = x + 1
        y = 0
        while rf.updates[y][U_TIME] > oe.start and y + 1 < rf.updates.__len__():
#            if y + 1 == rf.updates.__len__():
#                logging.error('reached end of updates. y = ' + str(y) + ' U_TIME - oe.start = ' + str(rf.updates[y][U_TIME] - oe.start))
#                break;
            y = y + 1
        logging.error('New episode (' + str(e) + '). Fragment skipped ' + str(x) + ' updates. New episode length is ' + str(y) + ' updates long. (' + str(rf.updates.__len__()) + ' left)')
        logging.error('Episode updates span ' + str(rf.updates[0][U_TIME] - rf.updates[y][U_TIME]) + ' ms')
        oe.asks_ob = rf.asks_ob
        oe.bids_ob = rf.bids_ob
        oe.updates = deque (itertools.islice (rf.updates, 0, y))
        oe.ref_price = 0.5 * (oe.asks_ob.keys()[0] + oe.bids_ob.keys()[-1])
        return (rf, oe)


#        while rf.updates[0][U_TIME] - self.period > rf.start:
#            self.train_episode (rf)

    """
    Optimal_strategy (V, H, T, I, L) 
        For t = T to 0
            While (not end of data) 
                Transform (order book) -> o_1 ... o_R
                For i = 0 to I {
                    For a = 0 to L {
                        Set x = {t, i, o_1 ... o_R}
                            Simulate transition x -> y
                            Calculate c_im(x, a)
                            Look up argmax c(y, p)
                            Update c(<t, v, o_1 ... o_R>, a)
        Select the highest-payout action argmax c(y, p) in every state y to ouput optimal policy
    """
    def train_episode (self, t, oe, mode):
        for i in range (self.vol_rez):
            vol = self.volume * float(i + 1) / self.vol_rez
            for a in range (ACTIONS):
#                e = oe # deepcopy (oe)
                price = self.action_price (a, oe, mode)
                (c_im, remaining_vol) = self.immediate_cost(a, oe, mode, price, vol)
                i_y = int(math.floor(self.vol_rez * remaining_vol / self.volume))
                if i_y == 8:
                    i_y = 7
                self.update_cost (t, i, i_y, a, c_im)

    def action_price (self, action, e, mode):   # This is adapted from gym env, and should probably be put in a separate place.
                                                # Also, this is markedly different from the paper method of getting prices, which I don't understand.
        if action <= ALU_00625AV:
            no_deeper_than = self.average_volume * 2. ** (-action)
            v = 0
            volume = 0
            i = 0
            if mode == MLU_BUY:
                our_obkv = e.bids_ob.__reversed__()
                our_obd = e.bids_ob
            else:
                our_obkv = e.asks_ob.keys()
                our_obd = e.asks_ob
            for price in our_obkv:
                i = i + 1
                volume = our_obd[price]
                if v + volume > no_deeper_than:
                    if mode == MLU_BUY:
                        return price + PRICE_RESOLUTION
                    else:
                        return price - PRICE_RESOLUTION
                else:
                    v = v + volume
            logging.error('length of ob: ' + str(len(our_obd.keys())) + ' after ' + str(i) + ' iterations')
            assert False, 'v = ' + str(v) + ', volume = ' + str(volume) + ', no_deeper_than = ' + str(no_deeper_than) + ', action = ' + str(action)
        if mode == MLU_BUY:
            our0 = e.bids_ob.keys()[-1]
            their0 = e.asks_ob.keys()[0]
        else:
            our0 = e.asks_ob.keys()[0]
            their0 = e.bids_ob.keys()[-1]
        if action == ALU_NEAR:
            if mode == MLU_BUY:
                return our0 + PRICE_RESOLUTION
            else:
                return our0 - PRICE_RESOLUTION
        if action == ALU_MID:
            return (our0 + their0) // 2
        if action == ALU_FAR:
            if mode == MLU_BUY:
                return their0 - PRICE_RESOLUTION
            else:
                return their0 + PRICE_RESOLUTION

    def immediate_cost (self, a, oe, mode, price, vol):     # adapted from market_emulator.episode
        transactions = []

        # Check for collisions between the old environment and the action (Offense)
        i = 0
        if mode == MLU_BUY:
            while price >= oe.asks_ob.keys()[i]:
                if vol <= oe.asks_ob.values()[i]:
                    transactions.append({'price': oe.asks_ob.keys()[i], 'amount': vol})
                    return self.transactions_cost (transactions, mode, oe.ref_price)
                else:
                    transactions.append({'price': oe.asks_ob.keys()[i], 'amount': oe.asks_ob.values()[i]})
                    vol = vol - oe.asks_ob.values()[i]
                i = i + 1   # Why does this god forsaken language not support for loops?!
        else:
            while price <= oe.bids_ob.__reversed__()[i]:
#                if inventory <= self.f.ob_bids.values()[i]: # nope, use the hash
                if vol <= oe.bids_ob.values()[-i-1]: # nope, use the hash
                    transactions.append({'price': oe.bids_ob.__reversed__()[i], 'amount': vol})
                    return self.transactions_cost (transactions, mode, oe.ref_price)
                else:
                    transactions.append({'price': oe.bids_ob.__reversed__()[i], 'amount': oe.bids_ob.values()[-i-1]})
                    vol = vol - oe.bids_ob.values()[-i-1]
                i = i + 1   # Why does this god forsaken language not support for loops?!

        for u in oe.updates:                                            # Defence
            if u[U_UPT] == UPT_REMOVE:  # That can't collide
                continue
            if ((mode == MLU_BUY and (u[U_ORT] == ORT_SELL or u[U_ORT] == ORT_ASK) and u[U_RATE] <= price) or
                (mode == MLU_SELL and (u[U_ORT] == ORT_BUY  or u[U_ORT] == ORT_BID) and u[U_RATE] >= price)):
                if vol <= u[U_VOL]:
                    transactions.append({'price': price, 'amount': vol})
                    return self.transactions_cost (transactions, mode, oe.ref_price)
                else:
                    transactions.append({'price': price, 'amount': u[U_VOL]})

        return self.transactions_cost (transactions, mode, oe.ref_price)

    def transactions_cost (self, transactions, mode, ref_price):
        cost = 0
        for t in transactions:
            cost = cost + (t['price'] - ref_price) * t['amount']
        if mode == MLU_BUY:
            return cost
        else:
            return -cost
            
    def market_order_cost (self, oe):
        cost = np.zeros((2, self.rez_vol + 1), float)
        for t in range(self.rez_vol + 1):
            vol = 
            for mode in (MLU_BUY, MLU_SELL):
                if mode == MLY_BUY:
                    for o in oe.asks_ob.keys():
                        if oe.asks_ob[o] 
                else:
                    ob = oe.bids_ob

    def update_cost (self, t, i, a, c_im):
        pass

if __name__ == '__main__':
    RLExec ('../fragments/', 'BTC_ETH', 180000, 8, 10000000, 8, 1.6).train_all ()
