from gym.envs.registration import register

register(
    id='PoloniEnv-v0',
    entry_point='aoerl_gym_envs.poloni:PoloniEnv',
)

