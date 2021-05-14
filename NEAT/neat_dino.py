# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# References -
# 1. https://github.com/codewmax/NEAT-ChromeDinosaur
# 2. https://github.com/Paperspace/DinoRunTutorial
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# Import libraries
import pygame
from pygame import *
import os
import random
import math
import sys
import neat
import pandas as pd
import matplotlib.pyplot as plt
import time
# from draw_winner_net import *
from visualize import *
from neat.math_util import softmax
import numpy as np
import csv

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Global pygame functions used in the game
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Function to load image (pygame surface object)
def load_image(name, sizex=-1, sizey=-1, colorkey=None,):

    fullname = os.path.join('templates', name)
    image = pygame.image.load(fullname)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)

    if sizex != -1 or sizey != -1:
        image = pygame.transform.scale(image, (sizex, sizey))

    return (image, image.get_rect())


# Function to load sprite sheet (array of pygame surface objects) from media files
def load_sprite_sheet(
        sheetname,
        nx,
        ny,
        scalex=-1,
        scaley=-1,
        colorkey=None,
):
    fullname = os.path.join('templates', sheetname)
    sheet = pygame.image.load(fullname)
    sheet = sheet.convert()

    sheet_rect = sheet.get_rect()

    templates = []

    sizex = sheet_rect.width/nx
    sizey = sheet_rect.height/ny

    for i in range(0, ny):
        for j in range(0, nx):
            rect = pygame.Rect((j * sizex, i*sizey, sizex, sizey))
            image = pygame.Surface(rect.size)
            image = image.convert()
            image.blit(sheet, (0, 0), rect)

            if colorkey is not None:
                if colorkey is -1:
                    colorkey = image.get_at((0, 0))
                image.set_colorkey(colorkey, RLEACCEL)

            if scalex != -1 or scaley != -1:
                image = pygame.transform.scale(image, (scalex, scaley))

            templates.append(image)

    # get rectangle of one sub_image
    sprite_rect = templates[0].get_rect()

    return templates, sprite_rect


# Initialise pygame
pygame.init()




# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Global constraints used in the game
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

dino_imgs, _ = load_sprite_sheet('dino.png', 5, 1, 46, 40, -1)

RUNNING = [dino_imgs[2], dino_imgs[3]]

JUMPING = dino_imgs[0]

DUCKING_IMGS, _ = load_sprite_sheet('dino_ducking.png', 2, 1, 59, 40, -1)

small_cactus_imgs, _ = load_sprite_sheet('cacti-small.png', 3, 1, 40, 40, -1)
big_cactus_imgs, _ = load_sprite_sheet('cacti-big.png', 3, 1, 40, 40, -1)
SMALL_CACTUS = [small_cactus_imgs[0],
                small_cactus_imgs[1], small_cactus_imgs[2]]
LARGE_CACTUS = [big_cactus_imgs[0], big_cactus_imgs[1], big_cactus_imgs[2]]

BIRD_IMGS, _ = load_sprite_sheet('ptera.png', 2, 1, 46, 40, -1)

BG, _ = load_image('ground.png', -1, -1, -1)

FONT = pygame.font.Font('freesansbold.ttf', 20)

score_df = {
    "generation": [],
    'score': [],
    'time': []
}




# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes to define the various elements of the Dino Game
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Class for Dino in Dino Run
class Dinosaur:
    X_POS = 80
    Y_POS = 345
    JUMP_VEL = 8.5
    Y_POS_DUCK = 350

    def __init__(self, img=RUNNING[0]):
        # self.image = img
        # self.dino_run = True
        # self.dino_jump = False
        # self.jump_vel = self.JUMP_VEL
        self.rect = pygame.Rect(self.X_POS, self.Y_POS,
                                img.get_width(), img.get_height())
        self.color = (random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
        # self.step_index = 0
        self.duck_img = DUCKING_IMGS
        self.run_img = RUNNING
        self.jump_img = JUMPING

        self.dino_duck = False
        self.dino_run = True
        self.dino_jump = False

        self.step_index = 0
        self.jump_vel = self.JUMP_VEL
        self.image = img
        self.dino_rect = self.image.get_rect()
        # self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS

    def update(self):
        if self.dino_run:
            self.run()
        if self.dino_jump:
            self.jump()
        if self.dino_duck:
            self.duck()
        if self.step_index >= 10:
            self.step_index = 0

    def jump(self):
        self.image = JUMPING
        if self.dino_jump:
            self.rect.y -= 1.5*self.jump_vel
            self.jump_vel -= 0.9
        if self.jump_vel <= -self.JUMP_VEL:
            self.dino_jump = False
            self.dino_run = True
            self.dino_duck = False
            self.jump_vel = self.JUMP_VEL

    def duck(self):
        self.image = self.duck_img[self.step_index // 5]
        # self.dino_rect = self.image.get_rect()
        self.rect.x = self.X_POS
        self.rect.y = self.Y_POS_DUCK
        self.step_index += 1

    def run(self):
        self.image = RUNNING[self.step_index // 5]
        self.rect.x = self.X_POS
        self.rect.y = self.Y_POS
        self.step_index += 1

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.rect.x, self.rect.y))
        pygame.draw.rect(SCREEN, self.color, (self.rect.x,
                         self.rect.y, self.rect.width, self.rect.height), 2)
        for obstacle in obstacles:
            pygame.draw.line(SCREEN, self.color, (self.rect.x +
                             54, self.rect.y + 12), obstacle.rect.center, 2)


# Class for Obstacle (Ptera and Cactus) in Dino Run
class Obstacle:
    def __init__(self, image, number_of_cacti):
        self.image = image
        self.type = number_of_cacti
        self.rect = self.image[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    def update(self):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            obstacles.pop()

    def draw(self, SCREEN):
        SCREEN.blit(self.image[self.type], self.rect)


# Class for Small Cactus in Dino Run
class SmallCactus(Obstacle):
    def __init__(self, image, number_of_cacti):
        super().__init__(image, number_of_cacti)
        self.rect.y = 350


# Class for Large Cactus in Dino Run
class LargeCactus(Obstacle):
    def __init__(self, image, number_of_cacti):
        super().__init__(image, number_of_cacti)
        self.rect.y = 350


# Class for bird (Ptera) in Dino Run
class Bird(Obstacle):
    def __init__(self, image):
        self.type = 0
        super().__init__(image, self.type)
        self.rect.y = 310
        self.index = 0

    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        SCREEN.blit(self.image[self.index//5], self.rect)
        self.index += 1




# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# NEAT Algorithm Implementation
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Function to remove genome from the set of genomes after they have died
def remove(index):
    global max_fitness, winner

    max_fitness = 0
    winner = ge[index]
    ge[index].fitness += points

    if ge[index].fitness > max_fitness:
        max_fitness = ge[index].fitness
        winner = ge[index]

    dinosaurs.pop(index)
    ge.pop(index)
    nets.pop(index)


# Function to compute the eucledian distance
def distance(pos_a, pos_b):
    dx = pos_a[0]-pos_b[0]
    dy = pos_a[1]-pos_b[1]
    return math.sqrt(dx**2+dy**2)


# Function to run the NEAT algorithm
def eval_genomes(genomes, config):
    global game_speed, x_pos_bg, y_pos_bg, obstacles, dinosaurs, ge, nets, points, counter, n

    clock = pygame.time.Clock()
    points = 0
    counter = 0
    n = 12
    obstacles = []
    dinosaurs = []
    ge = []
    nets = []

    x_pos_bg = 0
    y_pos_bg = 380
    game_speed = 10

    for genome_id, genome in genomes:
        dinosaurs.append(Dinosaur())
        ge.append(genome)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        # print("genome id:", genome_id)
        genome.fitness = 0
        # print("fitness:", genome.fitness)

    # Function to update score and game speed
    def score():
        global points, game_speed, counter, n

        if counter % n == n-1:
            points += 1
        if counter % 100 == 0:
            game_speed += 1
            n -= 1
            if n == 1:
                n = 2
        text = FONT.render(f'Points:  {str(points)}', True, (0, 0, 0))
        SCREEN.blit(text, (450, 50))

        if points % 50 == 0:
            row = [pop.generation+1, points]
            with open("scores_common_neat.csv", 'a') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(row)
            csvfile.close()

    # Function to update statistics of the NEAT algorithm
    def statistics():
        global dinosaurs, game_speed, ge
        text_1 = FONT.render(
            f'Dinosaurs Alive:  {str(len(dinosaurs))}', True, (0, 0, 0))
        text_2 = FONT.render(
            f'Generation:  {pop.generation+1}', True, (0, 0, 0))
        text_3 = FONT.render(
            f'Game Speed:  {str(game_speed)}', True, (0, 0, 0))

        SCREEN.blit(text_1, (50, 450))
        SCREEN.blit(text_2, (50, 480))
        SCREEN.blit(text_3, (50, 510))

    # Function to update background
    def background():
        global x_pos_bg, y_pos_bg
        image_width = BG.get_width()
        SCREEN.blit(BG, (x_pos_bg, y_pos_bg))
        SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
        if x_pos_bg <= -image_width:
            x_pos_bg = 0
        x_pos_bg -= game_speed

    run = True
    obstacle_type = 0
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        SCREEN.fill((255, 255, 255))

        for dinosaur in dinosaurs:
            dinosaur.update()
            dinosaur.draw(SCREEN)
        counter += 1
        if len(dinosaurs) == 0:
            break

        # Logic to update obstacles
        if len(obstacles) == 0:
            rand_int = random.randint(0, 2)
            if rand_int == 0:
                obstacles.append(SmallCactus(
                    SMALL_CACTUS, random.randint(1, 2)))
                obstacle_type = 0
            elif rand_int == 1:
                obstacles.append(LargeCactus(
                    LARGE_CACTUS, random.randint(1, 2)))
                obstacle_type = 0
            else:
                obstacles.append(Bird(BIRD_IMGS))
                obstacle_type = 1

        # Logic for collision of dino and obstacle
        for obstacle in obstacles:
            obstacle.draw(SCREEN)
            obstacle.update()
            for i, dinosaur in enumerate(dinosaurs):
                if dinosaur.rect.colliderect(obstacle.rect):
                    ge[i].fitness -= 1
                    remove(i)
                else:
                    ge[i].fitness += 1

        # Get the output from the gene (ANN) after feeding necessary inputs
        for i, dinosaur in enumerate(dinosaurs):
            output = nets[i].activate((dinosaur.rect.y,
                                       distance((dinosaur.rect.x, dinosaur.rect.y),
                                                obstacle.rect.midtop), obstacle.rect.y, obstacle_type, game_speed))

            # Perform duck or jump according to the ouput
            if output[0] > 0.5 and dinosaur.rect.y == dinosaur.Y_POS:
                dinosaur.dino_jump = True
                dinosaur.dino_run = False
                dinosaur.dino_duck = False
            if output[1] > 0.5 and dinosaur.rect.y == dinosaur.Y_POS:
                dinosaur.dino_jump = False
                dinosaur.dino_run = False
                dinosaur.dino_duck = True
            elif (output[1] < 0.5) and dinosaur.rect.y == dinosaur.Y_POS_DUCK:
                # print("Run")
                dinosaur.dino_jump = False
                dinosaur.dino_duck = False
                dinosaur.dino_run = True

        statistics()
        score()
        # print(genome.fitness)

        background()
        clock.tick(30)
        pygame.display.update()


# Setup the NEAT Neural Network
def run(config_path):
    global pop, config
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    pop = neat.Population(config)
    winner = pop.run(eval_genomes, 50)
    node_names = {}
    names = ['Dino Y', 'Dist from Obstacle',
             'Obstacle Y', 'Obstacle Type', 'Game Speed']
    n = 0
    for k in config.genome_config.input_keys:
        node_names[k] = names[n]
        n += 1

    draw_net(config, winner, True, fmt='png',
             filename="winnernet", node_names=node_names)



if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')

    fields = ['generation', 'score']
    with open("scores_common_neat.csv", 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)

    run(config_path)
