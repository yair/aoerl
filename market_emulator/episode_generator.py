from __future__ import absolute_import, division, print_function

import numpy as np
import logging

from market_emulator.episode import Episode
from market_emulator.fragment_generator import FragmentGenerator
from market_emulator.fragment_index import FragmentIndex

class EpisodeGenerator:     # TODO: Handle consecutive 'mini-fragments'
    def __init__ (self, market, basefragdir, period):
        self.period = period
        self.market = market
        self.basefragdir = basefragdir
#        self.findex = FragmentGenerator(market, basefragdir).index
        self.findex = FragmentIndex(market, basefragdir)
        self.skip_beginning = 0
        self.skip_ending = period

        self.generate_spans ()

    def generate_spans (self):
        self.total_interval = 0.
        self.spans = []
        for f_fro, f_to in self.findex.index.items():
            to = int(f_to) - self.skip_ending
            fro = int(f_fro) + self.skip_beginning
            if (to < fro):
                logging.error("Fragment " + str(f_fro) + ".pickle too short (" + str(f_to - f_fro) + ") for periods of length " + self.period)
                continue
            self.total_interval = self.total_interval + (to - fro)
            self.spans.append ({'from': fro, 'to': to, 'span': (to - fro), 'fragment': f_fro })
            logging.error('Fragment ' + str(fro) + ' spans ' + str(to - fro) + 'ms')
            
    def get_random_episode (self):
        point = np.random.random_sample() * self.total_interval;
        for span in self.spans:
            if point > span['span']: # Wonderful Span
                point -= span['span']
                continue
            return Episode(self.basefragdir + self.market + "/" + span['fragment'] + ".pickle", point, self.period)
        assert False
