import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np
import logging
import math

from market_emulator.episode_generator import EpisodeGenerator
from market_emulator.episode import Episode

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

class PoloniEnv (gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__ (self):
        self.observation_space = spaces.Box (low=0., high=1., shape=(2,), dtype=np.float32) # time left (monotonouosly decreasing) and inventory left (same)
        self.action_space = spaces.Box (low=0., high=1., shape=(1,), dtype=np.float32) # Aggressiveness (discretized into strategies)
#        self.action_space = spaces.Discrete(8) # [-1*AV, -.5*AV, -.25*AV, -.125*AV, -.0625*AV, bottom, middle, top]
        self.configure()
        self.reset()
        pass

    def configure (self):
        self.period = 180000 # milliseconds
        self.market = 'BTC_ETH'
#        self.average_volume = 1.6 # BTC per period
#        self.full_inventory = 0.1 # BTC     # TODO: bracketing
        self.average_volume = 160000000 # satoshi per period
        self.full_inventory = 10000000  # satoshi # TODO: bracketing
#        self.fragment_generator = FragmentGenerator (self.market, '../fragments') # TODO: seed
        self.episode_generator = EpisodeGenerator (self.market, '../fragments/', self.period) # TODO: seed

    def seed (self, seed):
        self.seed = seed

    def calc_reward (self, transactions):
        r = 0
        for t in transactions:
            r = r + 100 * ((t['price'] - self.benchmark_price) / self.benchmark_price) * (t['amount'] / self.full_inventory) # In percents now. :/
        if self.mode == MLU_BUY:
            r = r * -1
        return r

    def step(self, action):
        # calc next order
        logging.error('action type is ' + str(type(action)))
        price = self.action_price (int (math.floor (action * 8)))
        (self.remaining_time, self.inventory, transactions) = self.episode.step (self.inventory, price)
        reward = self.calc_reward (transactions)
        # TODO: handle transaction (calc reward)
        if self.remaining_time <= 0 and self.inventory > 0:
            logging.error ('* * *')
            logging.error ('* * * Executing a market order')
            logging.error ('* * *')
            transactions = self.episode.market_order (self.inventory)
            reward = reward + self.calc_reward (transactions)
            self.inventory = 0
        logging.error ('env.step returning: ' + str(((self.remaining_time, self.inventory), reward, self.inventory <= 0, {})) + ' A:' + str(action) + '->' + str(int(math.floor(action * 8))))
        return (self.remaining_time, self.inventory), reward, self.inventory <= 0, {}

    def reset(self):
        self.inventory = self.full_inventory
        self.remaining_time = self.period
        self.episode = self.episode_generator.get_random_episode () # TODO: these takes ages. Recycle sometimes.
        self.mode = MLU_BUY # np.random.randint(0, 2)
        self.episode.set_mode (self.mode)
        self.benchmark_price = (self.episode.f.asks_ob.keys()[0] + self.episode.f.bids_ob.keys()[-1]) // 2
        assert self.mode == MLU_BUY or self.mode == MLU_SELL
        if self.mode == MLU_BUY:
            self.our_obkv = self.episode.f.bids_ob.__reversed__()
            self.our_obd  = self.episode.f.bids_ob
            self.their_obkv = self.episode.f.asks_ob.keys()
            self.their_obd  = self.episode.f.asks_ob
        else:
            self.our_obkv = self.episode.f.asks_ob.keys()
            self.our_obd = self.episode.f.asks_ob
            self.their_obkv = self.episode.f.bids_ob.__reversed__()
            self.their_obd  = self.episode.f.bids_ob
        return (self.remaining_time, self.inventory)

    def render(self, mode='human', close=False):
        pass

    def action_price (self, action):
#        if action[0] <= ALU_00625AV:
        if action <= ALU_00625AV:
            no_deeper_than = self.average_volume * 2. ** (-action)
            v = 0
            volume = 0
            i = 0
            if self.mode == MLU_BUY:
                self.our_obkv = self.episode.f.bids_ob.__reversed__()
            else:
                self.our_obkv = self.episode.f.asks_ob.keys()
            for price in self.our_obkv:
                i = i + 1
                volume = self.our_obd[price]
                if v + volume > no_deeper_than:
                    if self.mode == MLU_BUY:
                        return price + PRICE_RESOLUTION
                    else:
                        return price - PRICE_RESOLUTION
                else:
                    v = v + volume
            logging.error('length of ob: ' + str(len(self.our_obd.keys())) + ' after ' + str(i) + ' iterations')
            assert False, 'v = ' + str(v) + ', volume = ' + str(volume) + ', no_deeper_than = ' + str(no_deeper_than) + ', action = ' + str(action)
        if self.mode == MLU_BUY:
            our0 = self.our_obd.keys()[-1]
            their0 = self.their_obd.keys()[0]
        else:
            our0 = self.our_obd.keys()[0]
            their0 = self.their_obd.keys()[-1]
        if action == ALU_NEAR:
            if self.mode == MLU_BUY:
                return our0 + PRICE_RESOLUTION
            else:
                return our0 - PRICE_RESOLUTION
        if action == ALU_MID:
            return (our0 + their0) // 2
        if action == ALU_FAR:
            if self.mode == MLU_BUY:
                return their0 - PRICE_RESOLUTION
            else:
                return their0 + PRICE_RESOLUTION
            """
    def action_price (self, action):
        if action[0] <= ALU_00625AV:
            no_deeper_than = self.average_volume * 2 ** (-action[0])
            v = 0
            for price, volume in self.our_ob.items():
                if v + volume > no_deeper_than:
                    if self.mode == MLU_BUY:
                        return price + PRICE_RESOLUTION
                    else:
                        return price - PRICE_RESOLUTION
                else:
                    v = v + volume
            assert False
        if action[0] == ALU_NEAR:
            if self.mode == MLU_BUY:
                return self.our_ob.keys()[0] + PRICE_RESOLUTION
            else:
                return self.our_ob.keys()[0] - PRICE_RESOLUTION
        if action[0] == ALU_MID:
            return (self.our_ob.keys()[0] + self.their_ob.keys()[0]) // 2
        if action[0] == ALU_FAR:
            if self.mode == MLU_BUY:
                return self.their_ob.keys()[0] - PRICE_RESOLUTION
            else:
                return self.their_ob.keys()[0] + PRICE_RESOLUTION
                """
