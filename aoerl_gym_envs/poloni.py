import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

from market_emulator.fragment import Fragment, FragmentGenerator

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
        self.episode_generator = EpisodeGenerator (self.market, '../fragments', self.period) # TODO: seed

    def seed (self, seed):
        self.seed = seed

    def step(self, action):
        pass

    def reset(self):
        self.inventory = self.full_inventory
        self.remaining_time = self.period
        self.episode = self.episode_generator.get_random_episode (self.period)
        pass

    def render(self, mode='human', close=False):
        pass
