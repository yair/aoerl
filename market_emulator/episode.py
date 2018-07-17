from __future__ import absolute_import, division, print_function

import logging

#from market_emulator.fragment import Fragment
from market_emulator.fragment import *

class Episode:
    def __init__ (self, fragment_fn, offset, period):
        self.f = Fragment (fragment_fn)
        self.offset = offset    # in millisecond, yes?
        self.period = period    # ditto, yes?
        assert self.f.start + offset <= self.f.end
        self.fstart = self.f.start
        self.estart = self.f.start + offset
        self.f.advance_to_time (self.estart)

    def set_mode (self, mode):
        self.mode = mode

    def step (self, inventory, price):
        transactions = []
#        remaining_time = self.f.updates[0][U_TIME] - self.estart # a bit of a cheat if we collide pre-step
        remaining_time = self.period + self.estart - self.f.updates[0][U_TIME] # a bit of a cheat if we collide pre-step
#        assert remaining_time >=0, 'remaining time: ' + str(remaining_time) + 'ms (' + str(self.period) + ' + ' + str(self.estart) + ' - ' + str(self.f.updates[0][U_TIME]) + ')' # This is wrong
        assert remaining_time <= self.estart + self.period
        assert inventory > 0, 'inventory is: ' + str(inventory)

        # Check for collisions between the old environment and the action (Offense)
        i = 0
        if self.mode == 0: # BUY
            while price >= self.f.asks_ob.keys()[i]:
                if inventory <= self.f.asks_ob.values()[i]:
                    transactions.append({'price': self.f.asks_ob.keys()[i], 'amount': inventory})
                    return (remaining_time, 0, transactions)
                else:
                    transactions.append({'price': self.f.asks_ob.keys()[i], 'amount': self.f.asks_ob.values()[i]})
                    inventory = inventory - self.f.asks_ob.values()[i]
                i = i + 1   # Why does this god forsaken language not support for loops?!
        else:
#            while price <= self.f.ob_bids.keys()[i]:
            while price <= self.f.bids_ob.__reversed__()[i]:
#                if inventory <= self.f.ob_bids.values()[i]: # nope, use the hash
                if inventory <= self.f.bids_ob.values()[-i-1]: # nope, use the hash
                    transactions.append({'price': self.f.bids_ob.__reversed__()[i], 'amount': inventory})
                    return (remaining_time, 0, transactions)
                else:
                    transactions.append({'price': self.f.bids_ob.__reversed__()[i], 'amount': self.f.bids_ob.values()[-i-1]})
                    inventory = inventory - self.f.bids_ob.values()[-i-1]
                i = i + 1   # Why does this god forsaken language not support for loops?!

        u = self.f.single_step ()
        assert u is not None
                                                                    # Defense
        if u[U_UPT] == UPT_REMOVE:  # That can't collide
            return (remaining_time, inventory, transactions)
        if ((self.mode == 0 and (u[U_ORT] == ORT_SELL or u[U_ORT] == ORT_ASK) and u[U_RATE] <= price) or
            (self.mode == 1 and (u[U_ORT] == ORT_BUY  or u[U_ORT] == ORT_BID) and u[U_RATE] >= price)):
            if inventory <= u[U_VOL]:
                transactions.append({'price': price, 'amount': inventory})
                return (remaining_time, 0, transactions)
            else:
                transactions.append({'price': price, 'amount': u[U_VOL]})
                return (remaining_time, inventory - u[U_VOL], transactions)
        return (remaining_time, inventory, transactions)

    def market_order (self, inventory):
        i = 0
        transactions = []
        ob = None
        obkeys = None
        if self.mode == 0: # BUY
            ob = self.f.asks_ob
            obkeys = self.f.asks_ob.keys()
        else:
            ob = self.f.bids_ob
            obkeys = self.f.bids_ob.__reversed__()

        while True:
            v = ob[obkeys[i]]
            if inventory <= v:
                transactions.append({'price': obkeys[i], 'amount': inventory})
                return transactions
            else:
                transactions.append({'price': obkeys[i], 'amount': v})
                inventory = inventory - v
            i = i + 1   # Why does this god forsaken language not support for loops?!
            """
        while True:
            if inventory <= self.f.ob_asks.values()[i]:
                transactions.append({price: self.f.ob_asks.keys()[i], amount: inventory})
                return transactions
            else:
                transactions.append({price: self.f.ob_asks.keys()[i], amount: self.f.ob_asks.values()[i]})
                inventory = inventory - self.f.asks_ob.values()[i]
            i = i + 1   # Why does this god forsaken language not support for loops?!
            """

        assert False
