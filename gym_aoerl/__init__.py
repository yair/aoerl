from gym.envs.registration import register

register(
    id='aoerl-poloni-v0',
    entry_point='gym_aoerl.envs:AoerlEnv',
)
