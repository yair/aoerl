from __future__ import absolute_import, division, print_function

import json
import logging
from sortedcontainers import SortedDict
import pickle
import os
import fnmatch

from market_emulator.fragment import Fragment

class FragmentIndex:
    def __init__ (self, market, basefragdir):
        self.market = market
        self.fragdir = basefragdir + market + "/"
        self.index_fn = self.fragdir + "index.json"
        self.load ()

    def load (self):
        if os.path.exists(self.index_fn):
            self.loaded = True
            with open (self.index_fn, 'r') as fh:
                self.index = json.load (fh)
        else:
            self.loaded = False

    def add_frag (self, frag):
#        assert frag.start not in self.index
        if frag.start in self.index:
            del self.index[frag.start]
        self.index[frag.start] = frag.end

    def save (self):
        with open (self.index_fn, 'w') as fh:
            json.dump (self.index, fh)

    def get_fragment (self, fro):
        return Fragment (self.fragdir + str(fro) + '.pickle')
