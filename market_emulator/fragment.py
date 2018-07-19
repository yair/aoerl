from __future__ import absolute_import, division, print_function

import logging
import pickle
from collections import deque

#class UpType (Enum):
UPT_MODIFY = 0
UPT_REMOVE = 1
UPT_NEW_TRADE = 2

#class OrType (Enum):
ORT_ASK = 0
ORT_BID = 1
ORT_BUY = 2
ORT_SELL = 3

#ob update tuple
U_TIME  = 0
U_UID   = 1
U_UPT   = 2
U_ORT   = 3
U_RATE  = 4
U_VOL   = 5

REZ = 100000000

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
        self.updates = deque()
        self.removes = 0
        self.modifies = 0

    def load_from_pickle (self, pickle_fn):
        with open (pickle_fn, 'rb') as fh:
            tmpfrag = pickle.load(fh)
            self.asks_ob = tmpfrag.asks_ob
            self.bids_ob = tmpfrag.bids_ob
            self.start = tmpfrag.start
            self.end = tmpfrag.end
            self.updates = deque (tmpfrag.updates)
            self.removes = 0
            self.modifies = 0

    def advance_to_time(self, time):
        logging.error("Advancing from " + str(self.start) + " to " + str(time))
        self.removes = 0
        self.modifies = 0
        while self.updates.__len__() > 0 and self.updates[0][U_TIME] <= time:
            self.single_step()
        logging.error('Advancing done after ' + str(self.removes) + ' removes and ' + str(self.modifies) + ' modifications')

    def single_step (self):
        u = self.updates.popleft()
        self.start = u[U_TIME]
        ob = None
        if u[U_UPT] == UPT_NEW_TRADE:
            return u    # That, on its own, doesn't affect the order books
        if u[U_ORT] == ORT_ASK:
            ob = self.asks_ob
        elif u[U_ORT] == ORT_BID:
            ob = self.bids_ob
        else:
            assert False, "u = " + str(u)
        if u[U_UPT] == UPT_REMOVE:
            assert u[U_RATE] in ob, 'About to remove ' + str(u[U_RATE]) + ' from ob, but it is not there'
            ob.pop(u[U_RATE])
            assert u[U_RATE] not in ob, 'Order at ' + str(u[U_RATE]) + ' still in ob after removal'
            self.removes = self.removes + 1
        elif u[U_UPT] == UPT_MODIFY:
            ob.update({u[U_RATE]: u[U_VOL]})
            assert u[U_RATE] in ob, 'Order at ' + str(u[U_RATE]) + ' not in ob after modification'
            self.modifies = self.modifies + 1
        else:
            assert False
        return u

    def get_ob (self, time):
        if (time < self.start or time > self.end):
            logging.error("get_ob: time given (" + time + ") outside of fragment range [" + self.start + ", " + self.end + "]")
            assert False
            return [];
        last_update = self.find_last_update (time)
        return run_to_update(last_update)
