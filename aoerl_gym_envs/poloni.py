import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

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

# Mode LookUp
MLU_BUY = 0
MLU_SELL = 1

PRICE_RESOLUTION = 1    # satoshi (whatabout BTC_USD?)

class PoloniEnv (gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__ (self):
        self.observation_space = spaces.Box (low=0., high=1., shape=(2,), dtype=np.float32) # time left (monotonouosly decreasing) and inventory left (same)
        self.action_space = spaces.Discrete(8) # [-1*AV, -.5*AV, -.25*AV, -.125*AV, -.0625*AV, bottom, middle, top]
        self.configure()
        self.reset()
        pass

    def configure (self):
        self.period = 180 # seconds
        self.market = 'BTC_ETH'
        self.average_volume = 1.6 # BTC per period
        self.full_inventory = 0.1 # BTC
#        self.fragment_generator = FragmentGenerator (self.market, '../fragments') # TODO: seed
        self.episode_generator = EpisodeGenerator (self.market, '../fragments/', self.period) # TODO: seed

    def seed (self, seed):
        self.seed = seed

    def step(self, action):
        # calc next order
        price = self.action_price (action)
        (self.remaining_time, self.inventory, transactions) = self.episode.step (self.inventory, price)
        # TODO: handle transaction (calc reward)
        if self.remaining_time <= 0 and self.inventory > 0:
            transactions = self.episode.market_order (self.inventory)
            # calc final reward

    def reset(self):
        self.inventory = self.full_inventory
        self.remaining_time = self.period
        self.episode = self.episode_generator.get_random_episode ()
        self.mode = np.random.randint(0, 2)
        self.episode.set_mode (self.mode)
        assert self.mode == MLU_BUY or self.mode == MLU_SELL
        if self.mode == MLU_BUY:
            self.our_ob = self.episode.f.bids_ob
            self.their_ob = self.episode.f.asks_ob
        else:
            self.our_ob = self.episode.f.asks_ob
            self.their_ob = self.episode.f.bids_ob # Should be inverted!

    def render(self, mode='human', close=False):
        pass

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
