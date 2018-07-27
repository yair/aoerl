from os import listdir
from os.path import isfile, join
from fnmatch import fnmatch
from copy import deepcopy
import itertools
import time
import json
import os
#import thread Docs said it existed, natch
import threading
from multiprocessing import Process, Lock, Pool

import numpy as np
import math

from market_emulator.fragment import *

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.WARNING)

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
        self.volume = volume        # Amount to transact, in bitcoin satoshis
        self.vol_rez = vol_rez      # number of volume intervals
        self.fragdir = join (basefragdir, market)
#        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*[0123456789].pickle')])             # default - all
        self.frag_limit = 3
#        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*1530547986739.pickle')])             # 607 ep eth
#        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*1530224638648.pickle')])             # 14369 ep eth
        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*1528097393910.pickle')])             # 3842 ep usdt
#        self.frag_fns =  sorted([join (self.fragdir, fn) for fn in listdir(self.fragdir) if fnmatch (fn, '*1528097393690.pickle')])             # 3842 ep doge
        self.q = np.zeros((2, time_rez, vol_rez, ACTIONS), dtype=float)
        self.elen = float(self.period) / self.time_rez
        self.gen = 0. # Global Episode Number, for normalization
        self.average_volume = average_vol   # Average volume per period in this market, in bitcoin satoshis
        self.optimal_actions = np.zeros((2, time_rez, vol_rez), dtype=int)
        self.market = market

    def train_all (self):
        for i in range(self.time_rez - 1, -1, -1):  # The only time that _should_ be reversed is the internal q-table intervals
            logging.error('============================================================')
            logging.error('Now calculating ' + self.market + ' optimal action for time step ' + str(i+1) + '/' + str(self.time_rez))
            logging.error('============================================================')
            self.gen = 0
            fnu = 0
            for fn in self.frag_fns:
                self.train_fragment (i, Fragment (fn))
                if self.frag_limit > 0:
                    fnu = fnu + 1
                    if fnu >= self.frag_limit:
                        break

            self.calc_optimal_actions (i)
            logging.info('Q = ' + str(self.q))
        self.dump_results ()

    def train_fragment (self, i, f):
        episodes = int(math.floor((f.end - f.start) / self.elen))
        f.orig_start = f.start
        logging.warning('This fragment (' + str(f.start) + ') contains ' + str(episodes) + ' episodes of ' + str(self.elen) + 'ms')
        gettime = motime = traintime = 0
        fen = self.gen
        for eid in range (episodes):
            a = time.time()
            (f, e) = self.get_episode (f, eid)
            if self.market == 'USDT_BTC':
                e.volume = self.volume
                e.average_volume = self.average_volume
            else:
                e.volume = 100000000 * self.volume / e.ref_price    # e.volume is in alt satoshis (ref_price is in whole alts per bsatoshis)
                e.average_volume = 100000000 * self.average_volume / e.ref_price
            b = time.time()
            e.mo_cost = self.market_order_cost (e)
            c = time.time()
            self.train_episode (i, e, MLU_BUY)
            self.train_episode (i, e, MLU_SELL)
            d = time.time()
            self.gen = self.gen + 1
            gettime = gettime + b - a
            motime = motime + c - b
            traintime = traintime + d - c
        logging.warning('fetching episode took on avg ' + str (1000*gettime/(self.gen-fen)) + 'ms. Moing took ' + str(1000*motime/(self.gen-fen)) + 'ms. Training took ' + str (1000*traintime/(self.gen-fen)) + 'ms.')

    def get_episode (self, f, eid):
        x = 0
        e = Fragment (None)
        e.start = f.orig_start + eid * self.elen
        e.end = f.orig_start + (eid + 1) * self.elen
        while f.updates[0][U_TIME] < e.start:
            f.single_step ()
            x = x + 1
        y = 0
        while f.updates[y][U_TIME] < e.end and y + 1 < f.updates.__len__():
            y = y + 1
        logging.info('New episode (' + str(e) + '). Fragment skipped ' + str(x) + ' updates. New episode length is ' + str(y) + ' updates long. (' + str(f.updates.__len__()) + ' left)')
        logging.info('Episode updates span ' + str(f.updates[y][U_TIME] - f.updates[0][U_TIME])  + ' ms')
        e.asks_ob = f.asks_ob
        e.bids_ob = f.bids_ob
        e.ref_price = 0.5 * (e.asks_ob.keys()[0] + e.bids_ob.keys()[-1])
        e.updates = deque (itertools.islice (f.updates, 0, y))
#        e.updates = self.prune (e) # Can't understand why it warps the results
        return (f, e)

    def prune (self, e):
        v = 0
        for p in e.bids_ob.__reversed__():
#            if v + e.bids_ob[p] > self.average_volume + self.volume:
            if v > self.average_volume + self.volume:
                minbid = p
                break
            v = v + e.bids_ob[p]
        v = 0
        for p in e.asks_ob.keys():
#            if v + e.asks_ob[p] > self.average_volume + self.volume:
            if v > self.average_volume + self.volume:
                maxask = p
                break
            v = v + e.asks_ob[p]
        logging.info('Pruning updates outside the range [' + str(minbid) + ' -(' + str(e.ref_price) + ')- ' + str(maxask) + ']')
        r = deque()

        for u in e.updates:
            if (u[U_UPT] == UPT_REMOVE or
#                    (u[U_RATE] > maxask and u[U_ORT] == ORT_ASK) or
#                    (u[U_RATE] < minbid and u[U_ORT] == ORT_BID)):
                    ((u[U_ORT] == ORT_ASK or u[U_ORT] == ORT_BID) and
                     (u[U_RATE] > maxask or u[U_RATE] < minbid))):
                logging.debug('pruning update ' + str(u))
                continue
            r.append(u)
        logging.info ('Episode update stream reduced from ' + str(len(e.updates)) + ' to ' + str(len(r)))
        return r  

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
            logging.debug('ref_price = ' + str(oe.ref_price) + 'bsat')
            for a in range (ACTIONS):
#                vol = self.volume * float(i + 1) / self.vol_rez
                vol = oe.volume * float(i + 1) / self.vol_rez
                price = self.action_price (a, oe, mode)
                (remaining_vol, c_im) = self.immediate_cost(a, oe, mode, price, vol)
#                i_y = int (round (self.vol_rez * remaining_vol / self.volume)) - 1  # <= [-1, i]. -1 means no further costs
                i_y = int (round (self.vol_rez * remaining_vol / oe.volume)) - 1  # <= [-1, i]. -1 means no further costs
                # correct cost quantization error
                logging.debug('mode='+str(mode)+' t='+str(t)+' i='+str(i)+' vol='+str(vol)+'altsat a='+str(a)+' price='+str(price)+'bsat rem='+str(remaining_vol)+'altsat c_im='+str(c_im)+'bp i_y='+str(i_y))
                """
                if i_y == i:    # Trading below threshold (volume < half resolution)
                    logging.debug ('c_im = ' + str(c_im) + ' ==> 0 (i_y == i)')
                    c_im = 0
                else:
                    if remaining_vol > 0:
                        logging.debug('cc_im = c_im * ((i - i_y) * self.volume / self.vol_rez) / (vol - remaining_vol) = ' + str(c_im) + ' * ((' + str(i) + ' - ' + str(i_y) + ') * ' + str(self.volume) + ' / ' + str(self.vol_rez) + ') / (' + str(vol) + ' - ' + str(remaining_vol) + ') = ' + str(c_im * ((i - i_y) * self.volume / self.vol_rez) / (vol - remaining_vol)))
                        c_im = c_im * ((i - i_y) * self.volume / self.vol_rez) / (vol - remaining_vol)
                    else:
                        logging.debug ('No need for correction, no volume remains')
                """
                self.update_cost (mode, t, oe, i, i_y, a, c_im)

    def action_price (self, action, e, mode):   # This is adapted from gym env, and should probably be put in a separate place.
                                                # Also, this is markedly different from the paper method of getting prices, which I don't understand.
        if action <= ALU_00625AV:
#            no_deeper_than = self.average_volume * 2. ** (-action)
            no_deeper_than = e.average_volume * 2. ** (-action)
            logging.debug ('no_deeper_than = ' + str(no_deeper_than) + 'altsat')
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
                logging.debug('price = ' +str(price) + 'bsat => v + volume = ' + str(v) + 'altsat + ' + str(volume) + 'altsat')
                if v + volume > no_deeper_than:
                    if mode == MLU_BUY:
                        if price + PRICE_RESOLUTION >= e.asks_ob.keys()[0]: # Don't overstep into their ob too soon
                            return price
                        else:
                            return price + PRICE_RESOLUTION
                    else:
                        if price - PRICE_RESOLUTION <= e.bids_ob.keys()[-1]:
                            return price
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
        logging.debug('our0 = ' + str(our0) + 'bsat their0 = ' + str(their0) + 'bsat')
        if action == ALU_NEAR:
            if mode == MLU_BUY:
                if our0 + PRICE_RESOLUTION >= their0:
                    return our0
                else:
                    return our0 + PRICE_RESOLUTION
            else:
                if our0 - PRICE_RESOLUTION <= their0:
                    return our0
                else:
                    return our0 - PRICE_RESOLUTION
        if action == ALU_MID:
            if mode == MLU_BUY:
                if (our0 + their0) // 2 >= their0:
                    return their0 - PRICE_RESOLUTION
                else:
                    return (our0 + their0) // 2
            else:
                if (our0 + their0) // 2 <= their0:
                    return their0 + PRICE_RESOLUTION
                else:
                    return (our0 + their0) // 2
        if action == ALU_FAR:
            if mode == MLU_BUY:
                return their0 - PRICE_RESOLUTION
            else:
                return their0 + PRICE_RESOLUTION

    def immediate_cost (self, a, oe, mode, price, vol):     # adapted from market_emulator.episode
        transactions = []
        # Optimistic execution correction approximation
        front = 0
        if mode == MLU_BUY:
            if oe.bids_ob.keys()[-1] == price:
                front = oe.bids_ob[price]                       # accountantial
#                vol = vol * vol / (vol + oe.bids_ob[price])    # statistical (broken)
        else:
            if oe.asks_ob.keys()[0] == price:
                front = oe.asks_ob[price]
#                vol = vol * vol / (vol + oe.asks_ob[price])
        """                                                                                      Do we even have offense? Their is 0 lag and all our actions are def
        # Check for collisions between the old environment and the action (Offense)              (also broken, but will need to be fixed if and when we include actions in their ob)
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
            uvol = u[U_VOL]
            if ((mode == MLU_BUY and (u[U_ORT] == ORT_SELL or u[U_ORT] == ORT_ASK) and u[U_RATE] <= price) or
                (mode == MLU_SELL and (u[U_ORT] == ORT_BUY  or u[U_ORT] == ORT_BID) and u[U_RATE] >= price)):
                if front > 0:
                    if front > uvol:
                        front = front - uvol
                        continue
                    else:
                        uvol = uvol - front
                        front = 0
#                if vol <= u[U_VOL]:
                if vol <= uvol:
                    transactions.append({'price': price, 'amount': vol, 'type': 'd'})
                    logging.debug('Transacted all: ' + str(transactions[-1]))
                    return (0, self.transactions_cost (transactions, mode, oe.ref_price, oe))
                else:
                    transactions.append({'price': price, 'amount': uvol, 'type': 'd'})
                    logging.debug('Transacted some: ' + str(transactions[-1]))
                    vol = vol - uvol

        return (vol, self.transactions_cost (transactions, mode, oe.ref_price, oe))

    def transactions_cost (self, transactions, mode, ref_price, oe):
        cost = 0
        for t in transactions:
            if mode == MLU_BUY:
                if t['type'] == 'o':
                    cost = cost + (t['price'] - ref_price) * t['amount'] + 0.002 * t['price'] * t['amount']
                elif t['type'] == 'd':
                    cost = cost + (t['price'] - ref_price) * t['amount'] + 0.001 * t['price'] * t['amount']
                else:
                    assert False, 'transaction has no type'
            else:
                if t['type'] == 'o':
                    cost = cost - (t['price'] - ref_price) * t['amount'] + 0.002 * t['price'] * t['amount']
                elif t['type'] == 'd':
                    cost = cost - (t['price'] - ref_price) * t['amount'] + 0.001 * t['price'] * t['amount']
                else:
                    assert False, 'transaction has no type' + str(transactions)
#        cost = cost * 10000. / (ref_price * self.volume)
        cost = cost * 10000. / (ref_price * oe.volume)
        return cost
            
    def market_order_cost (self, oe):
        cost = np.zeros((2, self.vol_rez), float)
        for t in range(self.vol_rez):
            for mode in (MLU_BUY, MLU_SELL):
                transactions = []
#                vol = self.volume * (t + 1) / self.vol_rez
                vol = oe.volume * (t + 1) / self.vol_rez
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
                cost[mode][t] = self.transactions_cost (transactions, mode, oe.ref_price, oe)
        logging.debug('market order cost: ' + str(cost) + 'bp')
        return cost

    def update_cost (self, mode, t, oe, i, i_y, a, c_im):
        if t == self.time_rez - 1:
            if i_y < 0:     # volume depleted, no further costs
                prev_cost = 0
            else:
                prev_cost = oe.mo_cost[mode][i_y]
        else:
            if i_y < 0:     # volume depleted, no further costs
                prev_cost = 0
            else:
                prev_cost = self.q[mode][t+1][i_y][self.optimal_actions[mode][t+1][i_y]]
        logging.debug ('tot_cost = prev_cost + c_im = ' + str(prev_cost) + ' + ' + str(c_im) + ' = ' + str(prev_cost + c_im) + 'bp')
        self.q[mode][t][i][a] = self.q[mode][t][i][a] * self.gen / (self.gen + 1) + (prev_cost + c_im) * (1 / (self.gen + 1))

    def calc_optimal_actions (self, t):
        for mode in (MLU_BUY, MLU_SELL):
            for i in range (self.vol_rez):
#                self.optimal_actions[mode][t][i] = np.argmax (self.q[mode][t][i])
                self.optimal_actions[mode][t][i] = np.argmin (self.q[mode][t][i])

    def dump_results (self):
        dumpdir = join (join ('../rlexec_output/', str(int(time.time()))), self.market)
        if not os.path.exists(dumpdir):
            os.makedirs(dumpdir)
        with open (join (dumpdir, 'policy.json'), 'w') as fh:
            json.dump (self.optimal_actions.tolist(), fh, indent=None)
        with open (join (dumpdir, 'q.json'), 'w') as fh:
            json.dump (self.q.tolist(), fh, indent=2)
        with open (join (dumpdir, 'fragments.json'), 'w') as fh:
            json.dump (self.frag_fns, fh, indent=2)

def train_all_coins ():
    with open ('volumes.json', 'r') as fh:
        volumes = json.load (fh)
    for c in volumes.keys():
        RLExec ('../fragments/', c, 180000, 8, 10000000, 8, volumes[c]/10.).train_all ()    # avg_vol / 10
        
volumes = {}
#lock = threading.Lock()
lock = Lock()

"""
class THread (threading.Thread):
    def __init__(self, volumes):
        threading.Thread.__init__(self)
        self.volumes = volumes
#    def train_coins_thread (volumes):
"""
"""
def run (volumes):
    while True:
        lock.acquire()
#        if len(self.volumes) == 0:
        if len(volumes) == 0:
            lock.release()
            logging.error("no more coins")
            return
#            market = self.volumes.keys()[0]
#            volume = self.volumes.values()[0]
#        market = list(self.volumes)[0]
        market = list(volumes)[0]
        assert market != None
        logging.error ('market = ' + market)
#        volume = self.volumes[market]
        volume = volumes[market]
#        del self.volumes[market]
        del volumes[market]
#            market, volume = self.volumes.pop()
#        logging.error('Doing market ' + market + '. ' + str(len(self.volumes.keys())) + ' markets left')
        logging.error('Doing market ' + market + '. ' + str(len(volumes.keys())) + ' markets left')
        lock.release()
        RLExec ('../fragments/', market, 180000, 8, 10000000, 8, volume/100).train_all ()    # avg_vol / 10

def train_all_coins_threadedly ():
    noof_threads = 7
    with open ('volumes.json', 'r') as fh:
        volumes = json.load (fh)
    logging.error("processing " + str(len(volumes.keys())) + " markets")
    for t in range (noof_threads):
        Process(target=run, args=(volumes)).start()
#        TH = THread (volumes)
#        TH.__init__()
#        TH.start() #start_new_thread (train_coins_thread, volumes)
"""        


if __name__ == '__main__':
#    RLExec ('../fragments/', 'BTC_ETH', 180000, 8, 10000000, 8, 160000000).train_all ()    # avg_vol
#    RLExec ('../fragments/', 'BTC_ETH', 180000, 8, 10000000, 8, 16000000).train_all ()    # avg_vol / 10
#    RLExec ('../fragments/', 'BTC_ETH', 180000, 8, 10000000, 8, 1600000).train_all ()    # avg_vol / 100
#    RLExec ('../fragments/', 'BTC_ETH', 180000, 8, 10000000, 8, 4800000).train_all ()    # avg_vol / 30    <---
#    RLExec ('../fragments/', 'USDT_BTC', 180000, 8, 10000000, 8, 312500000).train_all ()   # avg_vol
    RLExec ('../fragments/', 'USDT_BTC', 180000, 8, 10000000, 8, 12500000).train_all ()    # avg_vol / 30
#    RLExec ('../fragments/', 'BTC_DOGE', 180000, 8, 10000000, 8, 18541666).train_all ()
#    RLExec ('../fragments/', 'BTC_DOGE', 180000, 8, 10000000, 8, 618055).train_all ()     # avg_vol / 30
#    train_all_coins ()
#     train_all_coins_threadedly ()
#    train_all_coins_processly()
    
