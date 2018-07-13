# From the sarsa_cartpole keras-rl example
import numpy as np
import gym
import gym.spaces

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import Adam

from rl.agents import SARSAAgent
from rl.policy import BoltzmannQPolicy

from aoerl_gym_envs.poloni import PoloniEnv

ENV_NAME = 'PoloniEnv-v0'

# Get the environment and extract the number of actions.
env = gym.make(ENV_NAME)
np.random.seed(123)
env.seed(123)
nb_actions = env.action_space.n

