import sys
import random
import time
import math

import pygame
from pygame.locals import *

class MaritimeEnv():
    class Player(pygame.sprite.Sprite):
        def __init__(self, dimensions, initial_pos, velocity, color=(255, 0, 0)):
            super().__init__()
            self.surface = pygame.Surface((dimensions))
            self.rect = self.surface.get_rect(center=initial_pos)
            self.color = color
            self.velocity = velocity

            # Additional variable to track the USV's heading and previous heading. Heading is in radians
            self.heading = 0
            self.previous_heading = 0

        def move(self, heading_delta):
            # Calculate the USV's new heading wrt to the horizontal
            self.previous_heading = self.heading
            self.heading += heading_delta
            if self.heading < 0:
                self.heading += (2 * math.pi)
            
            elif self.heading > (2 * math.pi):
                self.heading -= (2* math.pi)

            # Calculate the change in x and y position of the USV
            # The sign of delta_y must be reversed since PyGame has positive y down instead of up
            delta_y = -1 * round(self.velocity * math.sin(self.heading), 0)
            delta_x = round(self.velocity * math.cos(self.heading), 0)

            # print(f'heading: {self.heading}')
            # print(f'delta y: {delta_y}')
            # print(f'delta x: {delta_x}')

            # Update the sprite's rectangle
            self.rect.move_ip(delta_x, delta_y)

        def calculate_radius(self, square_width):
            return (1 / math.sqrt(2)) * square_width

        def draw(self, surface):
            pygame.draw.circle(surface, self.color, self.rect.center, self.calculate_radius(self.rect.width))

    class Radar(Player):
        # The Radar should be transparent
        def __init__(self, dimensions, initial_pos, velocity, color=(148, 0, 211, 0.3)):
            super().__init__(dimensions, initial_pos, velocity, color)

    # Obstacle class
    class Obstacle(pygame.sprite.Sprite):
        # Dimensions = [x_center, y_center, width, height]
        def __init__(self, shape, dimensions, static=True, color=(0, 0, 0)):
            super().__init__()
            self.static = static
            # Size of obstacle
            self.surface = pygame.Surface((dimensions[2], dimensions[3]))
            # Location of obstacle
            self.rect = self.surface.get_rect(center=(dimensions[0], dimensions[1]))

            # Obstacle specifications
            self.shape = shape
            self.color = color

        def calculate_radius(self, square_width):
            return (1 / math.sqrt(2)) * square_width

        def draw(self, surface):
            if self.shape == 'rectangle':
                pygame.draw.rect(surface, self.color, self.rect)
            elif self.shape == 'circle':
                pygame.draw.circle(surface, self.color, self.rect.center, self.calculate_radius(self.rect.width))

    class Goal(pygame.sprite.Sprite):
        def __init__(self, dimensions, position, color=(0, 128, 0)):
            super().__init__()
            self.surface = pygame.Surface((dimensions[0], dimensions[1]))
            self.rect = self.surface.get_rect(center=position)
            self.color = color
            self.x = position[0]
            self.y = position[1]

        def calculate_radius(self, square_width):
            return (1 / math.sqrt(2)) * square_width
        
        def draw(self, surface):
            pygame.draw.circle(surface, self.color, self.rect.center, self.calculate_radius(self.rect.width))

    def __init__(self):
        # Initialise the pygame program
        pygame.init()

        # Set up colors
        self.RED = (255, 0, 0)
        self.SEA_BLUE = (173, 216, 230)
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)

        self.velocity = 5

        # Display dimensions
        self.DISPLAY_WIDTH = 600
        self.DISPLAY_HEIGHT = 600

        # Set up fonts
        self.font = pygame.font.SysFont("Verdana", 60)
        #self.font_small = pygame.font.SysFont("Verdana", 20)
        self.game_over = self.font.render("Game Over", True, self.BLACK)
        self.mission_success = self.font.render("Mission Success", True, self.BLACK)

        # Set up sprites
        self.create_sprites()

        # Create sprite groups
        self.create_sprite_groups()

        # Draw the initial game
        # todo - Only carry out this step if render is true
        pygame.display.set_caption("Maritime Environment")
        self.DISPLAY_SURF = pygame.display.set_mode((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))
        self.DISPLAY_SURF.fill(self.SEA_BLUE)
        for entity in self.all_sprites_group:
            entity.draw(self.DISPLAY_SURF)

        pygame.display.update()

        # Track whether it is game over or mission success
        self.game_over = False
        self.success = False

        # Track whether there are obstacles near the agent
        self.nearby_obstacles = False

        # Track the number of updates for an episode
        # If it exceeds 1000, reset the environment
        self.update_count = 0

    def create_sprites(self):
        self.player = self.Player(dimensions=(8,8), initial_pos=(75, 75), velocity=self.velocity)
        self.radar = self.Radar(dimensions = (100, 100), initial_pos=(75, 75), velocity=self.velocity)
        self.goal = self.Goal(dimensions=(200,200), position=(self.DISPLAY_WIDTH - 50, self.DISPLAY_HEIGHT - 50))
        self.obstacle_array = self.generate_static_obstacles(number=10, shapes=['rectangle', 'circle'],
                                                             max_proportion=0.15)

    def generate_static_obstacles(self, number, shapes, max_proportion, color=(0, 0, 0)):
        obstacle_array = []
        for i in range(number):
            while True:
                obstacle = self.generate_obstacle(shapes, max_proportion, color, static=True)
                # Check if the generated obstacle collides with player or goal
                if (not pygame.sprite.collide_rect(self.radar, obstacle)) and (not pygame.sprite.collide_rect(self.goal, obstacle)):
                    break
            
            obstacle_array.append(obstacle)

        return obstacle_array

    def generate_obstacle(self, shapes, max_proportion, color, static, random_seed=None):
        # This causes every obstacle generated to be the same
        shape = random.sample(shapes, 1)[0]
        x_coord = random.randint(0, self.DISPLAY_WIDTH)
        y_coord = random.randint(0, self.DISPLAY_HEIGHT)
        width = random.randint(1, self.DISPLAY_WIDTH * max_proportion)
        height = random.randint(1, self.DISPLAY_HEIGHT * max_proportion)

        # Create size specifications for the selected shape
        # [x_center, y_center, width, height]
        # width == height for drawing circles
        if shape == 'rectangle':
            dimensions = (x_coord, y_coord, width, height)
            obstacle = self.Obstacle(shape, dimensions, static=static, color=color)
        elif shape == 'circle':
            radius = width / 2
            dimensions = (x_coord, y_coord, radius, radius)
            obstacle = self.Obstacle(shape, dimensions, static=static, color=color)

        return obstacle

    def create_sprite_groups(self):
        self.all_sprites_group = pygame.sprite.Group()
        self.all_sprites_group.add(self.radar)
        self.all_sprites_group.add(self.player)
        self.all_sprites_group.add(self.goal)

        for obstacle in self.obstacle_array:
            self.all_sprites_group.add(obstacle)

        self.moving_sprites_group = pygame.sprite.Group()
        self.moving_sprites_group.add(self.player)
        self.moving_sprites_group.add(self.radar)

        self.obstacles_group = pygame.sprite.Group()
        for obstacle in self.obstacle_array:
            self.obstacles_group.add(obstacle)

    def end_game(all_sprites_group):
        pygame.display.update()
        for entity in all_sprites_group:
            entity.kill() 
        time.sleep(2)
        pygame.quit()
        sys.exit()
        
    def update(self, player, radar, action, goal, obstacles_group, all_sprites_group):
        self.DISPLAY_SURF.fill(self.SEA_BLUE)
        for entity in self.moving_sprites_group:
            entity.move(heading_delta=action)

        for entity in all_sprites_group:
            entity.draw(self.DISPLAY_SURF)
        pygame.display.update()

        self.check_collision(player, obstacles_group, collision_type='player')
        self.check_collision(radar, obstacles_group, collision_type='radar')

        self.check_success(player, goal)
        self.update_count += 1

    def check_collision(self, obj, obstacles_group, collision_type):
        obj_x, obj_y = obj.rect.center
        if (obj_x < 0) or (obj_x > self.DISPLAY_WIDTH) or (obj_y < 0) or (obj_y > self.DISPLAY_HEIGHT):
            # Game over if the collision type was with the player. If it is the radar then it doesn't matter
            if collision_type == 'player':
                self.game_over = True
            else:
                self.nearby_obstacles = True

            pygame.display.update()

        elif pygame.sprite.spritecollideany(obj, obstacles_group):
            if collision_type == 'player':
                self.game_over = True
            else:
                self.nearby_obstacles = True

            pygame.display.update()

        # If there is nothing in the radar after the collision checks
        else:
            self.nearby_obstacles = False

    def check_success(self, player, goal):
        if pygame.sprite.collide_rect(player, goal):
            self.success = True
            pygame.display.update()

    def reset(self):
        self.DISPLAY_SURF.fill(self.SEA_BLUE)
        self.game_over = False
        self.success = False
        self.update_count = 0

        # This might not be necessary
        for entity in self.all_sprites_group:
            entity.kill()

        self.create_sprites()
        self.create_sprite_groups()

        for entity in self.all_sprites_group:
            entity.draw(self.DISPLAY_SURF)
        pygame.display.update()

    def close(self):
        for entity in self.all_sprites_group:
            entity.kill()
        self.radar.kill()
        pygame.quit()
        # sys.exit()