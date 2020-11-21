from gym.envs.registration import register

register(
    id='static-maritime-v0',
    entry_point='static_maritime.envs:StaticMaritimeEnv',
)