from os import listdir
from os.path import isfile, join
from fnmatch import fnmatch
from copy import deepcopy
import itertools
import time
import json
import os

import numpy as np
import math

from market_emulator.fragment import *
#from market_emulator.reverse_fragment import ReverseFragment

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
#        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*reversed.pickle')])                 # reversed
#        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*1530547986739_reversed.pickle')])   # reversed
#        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*[0123456789].pickle')])             # default
        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*1530547986739.pickle')])
        self.q = np.zeros((2, time_rez, vol_rez, ACTIONS), dtype=float)
        self.elen = float(self.period) / self.time_rez
        self.gen = 0. # Global Episode Number, for normalization
        self.average_volume = average_vol
        self.optimal_actions = np.zeros((2, time_rez, vol_rez), dtype=int)

    def train_all (self):
        for i in range(self.time_rez - 1, -1, -1):  # The only time that _should_ be reversed is the internal q-table intervals
            logging.error('===================================================')
            logging.error('Now calculating optimal action for time step ' + str(i+1) + '/' + str(self.time_rez))
            logging.error('===================================================')
            self.gen = 0
            for fn in self.frag_fns:
#                self.train_fragment (i, ReverseFragment (fn))
                self.train_fragment (i, Fragment (fn))
            self.calc_optimal_actions (i)
            logging.error('Q = ' + str(self.q))
        self.dump_results ()

    def train_fragment (self, i, f):
        episodes = int(math.floor((f.end - f.start) / self.elen))
        f.orig_start = f.start
#        logging.error('This fragment contains ' + str(episodes) + ' episodes of ' + str(self.elen) + 'ms')
        # TODO: Drop first episode
#        for e in range (episodes - 1, -1, -1):      # reversed
        for eid in range (episodes):
            a = time.time()
            (f, e) = self.get_episode (f, eid)
            e.mo_cost = self.market_order_cost (e)
            b = time.time()
            self.train_episode (i, e, MLU_BUY)
            self.train_episode (i, e, MLU_SELL)
            c = time.time()
#            logging.error('fetching episode took ' + str (b-a) + 's. Training took ' + str (c-b) + 's')
            self.gen = self.gen + 1
#            self.train_episode (i, oe, MLU_SELL)

    def get_episode (self, f, eid):
        x = 0
#        e = ReverseFragment (None)
        e = Fragment (None)
        e.start = f.orig_start + eid * self.elen
        e.end = f.orig_start + (eid + 1) * self.elen
#        rf.updates = deque (itertools.islice (rf.updates, fro, to)...
        while f.updates[0][U_TIME] < e.start:
#            rf.updates.popleft ()   # WHY?!?! We need to do a proper fragment.single_step to update the order books.
            f.single_step () # Now that didn't doesn't advance at all. What is going on? it changes self.start. Bah. Why? Bah.
            x = x + 1
        y = 0
        while f.updates[y][U_TIME] < e.end and y + 1 < f.updates.__len__():
#            if y + 1 == rf.updates.__len__():
#                logging.error('reached end of updates. y = ' + str(y) + ' U_TIME - oe.start = ' + str(rf.updates[y][U_TIME] - oe.start))
#                break;
            y = y + 1
#        logging.error('New episode (' + str(e) + '). Fragment skipped ' + str(x) + ' updates. New episode length is ' + str(y) + ' updates long. (' + str(f.updates.__len__()) + ' left)')
#        logging.error('Episode updates span ' + str(f.updates[y][U_TIME] - f.updates[0][U_TIME])  + ' ms')
        e.asks_ob = f.asks_ob
        e.bids_ob = f.bids_ob
        e.updates = deque (itertools.islice (f.updates, 0, y))
        e.ref_price = 0.5 * (e.asks_ob.keys()[0] + e.bids_ob.keys()[-1])
        return (f, e)


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
#            vol = self.volume * float(i + 1) / self.vol_rez
            logging.debug('ref_price = ' + str(oe.ref_price))
            for a in range (ACTIONS):
                vol = self.volume * float(i + 1) / self.vol_rez
#                e = oe # deepcopy (oe)
                price = self.action_price (a, oe, mode)
                (remaining_vol, c_im) = self.immediate_cost(a, oe, mode, price, vol)
                i_y = int(math.floor(self.vol_rez * remaining_vol / self.volume))
                if i_y == 8:
                    i_y = 7
                logging.debug('mode='+str(mode)+' t='+str(t)+' i='+str(i)+' vol='+str(vol)+' a='+str(a)+' price='+str(price)+' rem='+str(remaining_vol)+' c_im='+str(c_im)+' i_y='+str(i_y))
                self.update_cost (mode, t, oe, i, i_y, a, c_im)

    def action_price (self, action, e, mode):   # This is adapted from gym env, and should probably be put in a separate place.
                                                # Also, this is markedly different from the paper method of getting prices, which I don't understand.
        if action <= ALU_00625AV:
            no_deeper_than = self.average_volume * 2. ** (-action)
            logging.debug ('no_deeper_than = ' + str(no_deeper_than))
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
                logging.debug(str(price) + ' - v + volume = ' + str(v) + ' + ' + str(volume))
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
        logging.debug('our0 = ' + str(our0) + ' their0 = ' + str(their0))
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
        """                                                                                      Do we even have offense? Their is 0 lag and all our actions are def
        # Check for collisions between the old environment and the action (Offense)              (also broken)
#        i = 0  # Why are keys iterable but reversed keys are not? (don't answer me)
        if mode == MLU_BUY:
#            while price >= oe.asks_ob.keys()[i]:       # god I hate this language
            for o in oe.asks_ob.keys():
                if o < price:
                    break
#                if vol <= oe.asks_ob.values()[i]:
                if vol <= oe.asks_ob[o]:
                    transactions.append({'price': o, 'amount': vol, 'type': 'o'})
                    logging.error('Bought all: ' + str(transactions[-1]))
                    return (0, self.transactions_cost (transactions, mode, oe.ref_price))
                else:
                    transactions.append({'price': o, 'amount': oe.asks_ob[o], 'type': 'o'})
                    logging.error('Bought some: ' + str(transactions[-1]))
                    vol = vol - oe.asks_ob[o]
#                i = i + 1   # Why does this god forsaken language not support for loops?!
        else:
#            while price <= oe.bids_ob.__reversed__()[i]:
            for o in oe.bids_ob.__reversed__():
                if price > o:
                    break
#                if inventory <= self.f.ob_bids.values()[i]: # nope, use the hash
#                if vol <= oe.bids_ob.values()[-i-1]: # nope, use the hash
                if vol <= oe.bids_ob[o]:
                    transactions.append({'price': o, 'amount': vol, 'type': 'o'})
                    logging.error('Sold all: ' + str(transactions[-1]))
                    return (0, self.transactions_cost (transactions, mode, oe.ref_price))
                else:
                    transactions.append({'price': o, 'amount': oe.bids_ob[o], 'type': 'o'})
                    logging.error('Sold some: ' + str(transactions[-1]))
                    vol = vol - oe.bids_ob[o]
#                i = i + 1   # Why does this god forsaken language not support for loops?!
        """
        for u in oe.updates:                                            # Defence
            if u[U_UPT] == UPT_REMOVE:  # That can't collide
                continue
            if ((mode == MLU_BUY and (u[U_ORT] == ORT_SELL or u[U_ORT] == ORT_ASK) and u[U_RATE] <= price) or
                (mode == MLU_SELL and (u[U_ORT] == ORT_BUY  or u[U_ORT] == ORT_BID) and u[U_RATE] >= price)):
                if vol <= u[U_VOL]:
                    transactions.append({'price': price, 'amount': vol, 'type': 'd'})
                    logging.debug('Transacted all: ' + str(transactions[-1]))
                    return (0, self.transactions_cost (transactions, mode, oe.ref_price))
                else:
                    transactions.append({'price': price, 'amount': u[U_VOL], 'type': 'd'})
                    logging.debug('Transacted some: ' + str(transactions[-1]))
                    vol = vol - u[U_VOL]

        return (vol, self.transactions_cost (transactions, mode, oe.ref_price))

    def transactions_cost (self, transactions, mode, ref_price):    # TODO: <-- this will make more sense if we round the volume to the nearest voxel
        cost = 0
        for t in transactions:
            if t['type'] == 'o':
                cost = cost + (t['price'] - ref_price) * t['amount'] + 0.002 * t['price'] * t['amount']
            elif t['type'] == 'd':
                cost = cost + (t['price'] - ref_price) * t['amount'] + 0.001 * t['price'] * t['amount']
            else:
                assert False, 'transaction has no type'
#        if mode == MLU_BUY:
        return cost     # Why is the cost positive for both modes? Odd. TODO: Investigate
#        else:
#            return -cost
            
    def market_order_cost (self, oe):
        cost = np.zeros((2, self.vol_rez), float)
        for t in range(self.vol_rez):
            for mode in (MLU_BUY, MLU_SELL):
                transactions = []
                vol = self.volume * (t + 1) / self.vol_rez
                if mode == MLU_BUY:
                    for o in oe.asks_ob.keys():
                        if oe.asks_ob[o] >= vol:
                            transactions.append({'price': o, 'amount': vol, 'type': 'o'})
                            break
                        else:
                            transactions.append({'price': o, 'amount': oe.asks_ob[o], 'type': 'o'})
                            vol = vol - oe.asks_ob[o]
                else:
                    for o in oe.bids_ob.__reversed__():
                        if oe.bids_ob[o] >= vol:
                            transactions.append({'price': o, 'amount': vol, 'type': 'o'})
                            break
                        else:
                            transactions.append({'price': o, 'amount': oe.bids_ob[o], 'type': 'o'})
                            vol = vol - oe.bids_ob[o]
                cost[mode][t] = self.transactions_cost (transactions, mode, oe.ref_price)
#        logging.error('market order cost: ' + str(cost))
        return cost

#        self.q = np.zeros((2, time_rez, vol_rez, ACTIONS), dtype=float)
    def update_cost (self, mode, t, oe, i, i_y, a, c_im):
        if t == self.time_rez - 1:
            prev_cost = oe.mo_cost[mode][i_y]
        else:
#            prev_cost = self.q[mode][t+1][i_y][np.argmax (self.q[mode][t+1][i_y])]  # TODO: calc offline
            prev_cost = self.q[mode][t+1][i_y][self.optimal_actions[mode][t+1][i_y]]  # TODO: calc offline
        self.q[mode][t][i][a] = self.q[mode][t][i][a] * self.gen / (self.gen + 1) + (prev_cost + c_im) * (1 / (self.gen + 1))

    def calc_optimal_actions (self, t):
        for mode in (MLU_BUY, MLU_SELL):
            for i in range (self.vol_rez):
                self.optimal_actions[mode][t][i] = np.argmax (self.q[mode][t][i])

    def dump_results (self):
        dumpdir = join ('../rlexec_output/', str(int(time.time())))
        if not os.path.exists(dumpdir):
            os.makedirs(dumpdir)
        with open (join (dumpdir, 'policy.json'), 'w') as fh:
            json.dump (self.optimal_actions.tolist(), fh, indent=None)
        with open (join (dumpdir, 'q.json'), 'w') as fh:
            json.dump (self.q.tolist(), fh, indent=2)
        with open (join (dumpdir, 'fragments.json'), 'w') as fh:
            json.dump (self.frag_fns, fh, indent=2)

if __name__ == '__main__':
    RLExec ('../fragments/', 'BTC_ETH', 180000, 8, 100000000, 8, 160000000).train_all ()
