from __future__ import absolute_import, division, print_function

import logging
import pickle
from collections import deque
from copy import deepcopy

from market_emulator.fragment import *

class ReverseFragment (Fragment):
    def existing_amount (self, f, u):
        if u[U_ORT] == ORT_ASK:
            if u[U_RATE] in f.asks_ob:
                return f.asks_ob[u[U_RATE]]
            else:
                return None
        elif u[U_ORT] == ORT_BID:
            if u[U_RATE] in f.bids_ob:
                return f.bids_ob[u[U_RATE]]
            else:
                return None
        else:
            assert False, 'Got bad update ' + str(u)

    def init_from_fragment (self, f):
        self.start = f.start
        self.end = f.end
        while f.updates.__len__() > 0:
#            logging.error("f.updates.__len__() = " + str(f.updates.__len__()))
            u = f.updates[0]
            my_u = ()
            if u[U_UPT] == UPT_REMOVE:  # This is an add for us, done by UPT_MODIFY
                my_u = (u[U_TIME], u[U_UID], UPT_MODIFY, u[U_ORT], u[U_RATE], self.existing_amount (f, u))
            elif u[U_UPT] == UPT_MODIFY:
                e = self.existing_amount (f, u)
                if e == None:           # This modify is actually add
                    my_u = (u[U_TIME], u[U_UID], UPT_REMOVE, u[U_ORT], u[U_RATE], 0)
                else:
                    my_u = (u[U_TIME], u[U_UID], UPT_MODIFY, u[U_ORT], u[U_RATE], e)
            elif u[U_UPT] == UPT_NEW_TRADE:
                my_u = None             # This doesn't change the ob on its own, right?
            else:
                assert False
            if my_u != None:
                self.updates.appendleft(my_u)
            f.single_step ()
        self.asks_ob = deepcopy (f.asks_ob)
        self.bids_ob = deepcopy (f.bids_ob)
