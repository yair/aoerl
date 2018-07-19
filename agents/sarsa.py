# From the sarsa_cartpole keras-rl example
import numpy as np
import gym
import gym.spaces
import time

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import Adam

#from rl.agents import SARSAAgent
from rl.agents import DDPGAgent
from rl.policy import BoltzmannQPolicy

from aoerl_gym_envs.poloni import PoloniEnv

ENV_NAME = 'PoloniEnv-v0'

# Get the environment and extract the number of actions.
env = gym.make(ENV_NAME)
np.random.seed(123)
env.seed(123)
nb_actions = 1 #env.action_space.n

# Next, we build a very simple model.
model = Sequential()
model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
model.add(Dense(4))
model.add(Activation('relu'))
model.add(Dense(4))
#model.add(Activation('relu'))
#model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dense(nb_actions))
#model.add(Activation('linear')) # linear? we want to restrict to [0, 1] range.
model.add(Activation('sigmoid')) # linear? we want to restrict to [0, 1] range.
print(model.summary())

# SARSA does not require a memory.
policy = BoltzmannQPolicy()
#sarsa = SARSAAgent(model=model, nb_actions=nb_actions, nb_steps_warmup=10, policy=policy)
sarsa = DDPGAgent(model=model, nb_actions=nb_actions, nb_steps_warmup=10, policy=policy)
sarsa.compile(Adam(lr=1e-3), metrics=['mae'])

# Okay, now it's time to learn something! We visualize the training here for show, but this
# slows down training quite a lot. You can always safely abort the training prematurely using
# Ctrl + C.
sarsa.fit(env, nb_steps=100, visualize=False, verbose=2)

# After training is done, we save the final weights.
sarsa.save_weights('sarsa_{}_{}_weights.h5f'.format(ENV_NAME, str(int(round(time.time())))), overwrite=False)

# Finally, evaluate our algorithm for 5 episodes.
#sarsa.test(env, nb_episodes=5, visualize=True)

