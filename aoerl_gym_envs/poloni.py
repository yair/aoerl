import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np

class PoloniEnv (gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__ (self):
        self.observation_space = spaces.Box (low=0., high=1., shape=(2,), dtype=np.float32)
        self.action_space = spaces.Discrete(8)
        pass

    def seed (self, seed):
        self.seed = seed

    def step(self, action):
        pass

    def reset(self):
        pass

    def render(self, mode='human', close=False):
        pass
