import gym
from gym import error, spaces, utils
from gym.utils import seeding

import math
import numpy as np
import time

from static_maritime.envs.static_maritime_game import MaritimeEnv

class StaticMaritimeEnv(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self, env_kwargs):
    # Initialise the car game object
    self.maritime_env = MaritimeEnv()

    # Define the action and observation space
    # Change in heading angle
    self.action_space = spaces.Box(low=np.array([-math.pi/18]), high=np.array([math.pi/18]))
    #self.action_space = spaces.Discrete(5)

    # x, y of player and x, y of the obstacle respectively
    self.observation_space = spaces.Box(low=np.array([0, 0, 0, 0, 0]),
                                        high=np.array([self.maritime_env.DISPLAY_WIDTH,
                                                       self.maritime_env.DISPLAY_HEIGHT,
                                                       2*math.pi,
                                                       self.maritime_env.DISPLAY_WIDTH,
                                                       self.maritime_env.DISPLAY_HEIGHT
                                                      ]
                                                     )
                                        )

    # Add in the weights and penalties

    self.heading_change_coef = env_kwargs['heading_delta_reward_coefficient']
    self.goal_distance_coef = env_kwargs['goal_distance_reward_coefficient']
    self.avoidance_reward = env_kwargs['avoidance_reward']
    self.game_over_penalty = env_kwargs['game_over_penalty']
    self.mission_success_reward = env_kwargs['success_reward']

    # x, y and heading
    agent_x, agent_y = self.maritime_env.player.rect.center
    self.state = np.array([agent_x, agent_y, self.maritime_env.player.heading, self.maritime_env.goal.x, self.maritime_env.goal.y])

  def step(self, action):
    # Get info from previous state to compare to new state
    prev_player_x, prev_player_y = self.maritime_env.player.rect.center
    prev_nearby_obstacles = self.maritime_env.nearby_obstacles

    # action_dict = {0: -10 * (math.pi/180), 1: -5 * (math.pi/180), 2: 0 * (math.pi/180), 3: 5 * (math.pi/180), 4: 10 * (math.pi/180)}
    # action = action_dict[action]
    #print(f'action: {action}')

    self.maritime_env.update(player=self.maritime_env.player, radar=self.maritime_env.radar, action=action,
                             goal=self.maritime_env.goal, obstacles_group=self.maritime_env.obstacles_group,
                             all_sprites_group=self.maritime_env.all_sprites_group)

    # Track if the episode is completed
    done = False
    # Track the reward gained in the episode
    reward = 0
    
    # Heading change reward function to minimise heading change
    # reward coefficient * absolute heading change
    reward -= self.heading_change_coef * abs(self.maritime_env.player.heading - self.maritime_env.player.previous_heading)

    # Distince from goal reward function
    # reward coefficient * euclidean distance from USV to goal
    player_x, player_y = self.maritime_env.player.rect.center
    goal_x, goal_y = self.maritime_env.goal.rect.center
    prev_goal_distance = math.sqrt((prev_player_x - goal_x)**2 + (prev_player_y - goal_y)**2)
    goal_distance = math.sqrt((player_x - goal_x)**2 + (player_y - goal_y)**2)

    if goal_distance < prev_goal_distance:
      reward += self.goal_distance_coef * abs(prev_goal_distance - goal_distance)
    else:
      reward -= self.goal_distance_coef * abs(goal_distance - prev_goal_distance)

    nearby_obstacles = self.maritime_env.nearby_obstacles
    # There were nearby obstacles and the agent moved away
    if prev_nearby_obstacles and not nearby_obstacles:
      reward += self.avoidance_reward
    # There were nearby obstacles and there are still nearby obstacles
    elif prev_nearby_obstacles and nearby_obstacles:
      reward -= self.avoidance_reward
    # There were no nearby obstacles but now there are
    elif not prev_nearby_obstacles and nearby_obstacles:
      reward -= self.avoidance_reward

    if (self.maritime_env.game_over) or (self.maritime_env.update_count >= 3000):
      reward -= self.game_over_penalty
      done = True

    elif self.maritime_env.success:
      reward += self.mission_success_reward
      done = True

    agent_x, agent_y = self.maritime_env.player.rect.center
    self.state = np.array([agent_x, agent_y, self.maritime_env.player.heading[0], self.maritime_env.goal.x, self.maritime_env.goal.y])

    info = {"goal_distance": math.sqrt((player_x - goal_x)**2 + (player_y - goal_y)**2)}

    # print(f'agent action: {action}')
    # print(f'agent reward: {reward}')

    #print(f'reward: {reward}')
    return self.state, reward, done, info
  def reset(self):
    self.maritime_env.reset()

    agent_x, agent_y = self.maritime_env.player.rect.center
    self.state = np.array([agent_x, agent_y, self.maritime_env.player.heading, self.maritime_env.goal.x, self.maritime_env.goal.y])
    return self.state

  def render(self, mode='human'):
    pass
  def close(self):
    self.maritime_env.close()