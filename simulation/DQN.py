# disable warning message
import logging
logging.getLogger('tensorflow').disabled = True

# disable "Using tensorflow backend" message
import sys
stderr = sys.stderr
sys.stderr = open('/dev/null', 'w')

from keras.optimizers import Adam
from keras.models import Sequential
from keras.layers.core import Dense, Dropout
sys.stderr = stderr

import random
import numpy as np
import pandas as pd
import os
import math
import util
from operator import add
 
class DQNMoveAgent(object):
  def __init__(self):
    self.epslion = 0
    self.reward = 0
    self.gamma = 0.9
    self.grid_size = 25
    self.dataframe = pd.DataFrame()
    self.short_memory = np.array([])
 
    self.avoid = False
    self.avoid_target = None
    self.old_target = None
    self.agency_target = 1
    self.agency_predict = 0
    self.shoot = False
    self.old_shoot = False
 
    self.learning_rate = 0.001
    weights = None
    if (os.path.isfile('./move_weights.hdf5')):
      weights = 'move_weights.hdf5'
    self.model = self.network(weights)
    self.eplison = 0
    self.actual = []
    self.memory = []
    self.prev_pos = {
      'x': 0,
      'y': 0
    }
    self.stopping = False
    self.stopping_step = 0
 
  def get_state(self, game):
    self.stopping = True
    # record previous position
    if not game.player_agent.position['x'] == self.prev_pos['x']:
      self.prev_pos['x'] = game.player_agent.position['x']
      self.stopping = False
      self.stopping_step = 0
    if not game.player_agent.position['y'] == self.prev_pos['y']:
      self.prev_pos['y'] = game.player_agent.position['y']
      self.stopping = False
      self.stopping_step = 0

    if self.stopping:
      self.stopping_step += 1

    # screen = pygame.surfarray.array2d(game.game_display)
    # return screen.reshape(screen.shape[0], screen.shape[1], 1)
    
    target_pos = util.dense_position(game, 5)
    state = [
      round(game.player_agent.position['x'] / game.game_width, 2), # x position
      round(game.player_agent.position['y'] / game.game_height, 2), # y position
      round(game.player_agent.velocity['x'] / math.sqrt(game.player_agent.status['move_speed'] + 5), 2), # x movement
      round(game.player_agent.velocity['y'] / math.sqrt(game.player_agent.status['move_speed'] + 5), 2), # y movement
      round(game.player_agent.acceleration['up'] / 10, 2), # up acceleration volumn
      round(game.player_agent.acceleration['down'] / 10, 2), # down acceleration volumn
      round(game.player_agent.acceleration['left'] / 10, 2), # left acceleration volumn
      round(game.player_agent.acceleration['right'] / 10, 2), # right acceleration volumn
      round(abs(game.player_agent.position['x'] - (game.game_width / 2)) / (game.game_width / 2), 2), # player_agent x distance ratio to center
      round(abs(game.player_agent.position['y'] - (game.game_width / 2)) / (game.game_height / 2), 2), # player_agent y distance ratio to center
      round(abs(game.player_agent.position['x'] - target_pos['x']) / game.game_width, 2), # target position x
      round(abs(game.player_agent.position['y'] - target_pos['y']) / game.game_height, 2), # target position y
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0
    ]
    # compute the grid-cell value
    v_x = 0 #max(game.player_agent.position['x'] - game.field['width'] / 2, 0)
    v_y = 0 #max(game.player_agent.position['y'] - game.field['height'] / 2, 0)
    player_x = game.player_agent.position['x']
    player_y = game.player_agent.position['y']
    
    weight = 0
    for stuff in game.map_info['stuffs']:
      if not util.distance(game.player_agent.position, stuff.position):
        continue
      weight += 1 / util.distance(game.player_agent.position, stuff.position)
      angle = util.angle(game.player_agent.position, stuff.position)
      angle += 2 * math.pi if angle < 0 else 0
      if 0 < angle <= math.pi / 4:
        state[12] += 1 / util.distance(game.player_agent.position, stuff.position)
      if math.pi / 4 < angle <= math.pi / 2:
        state[13] += 1 / util.distance(game.player_agent.position, stuff.position)
      if math.pi / 2 < angle <= math.pi / 4 * 3:
        state[14] += 1 / util.distance(game.player_agent.position, stuff.position)
      if math.pi / 4 * 3 < angle <= math.pi:
        state[15] += 1 / util.distance(game.player_agent.position, stuff.position)
      if math.pi < angle <= math.pi / 4 * 5:
        state[16] += 1 / util.distance(game.player_agent.position, stuff.position)
      if math.pi / 4 * 5 < angle <= math.pi / 2 * 3:
        state[17] += 1 / util.distance(game.player_agent.position, stuff.position)
      if math.pi / 2 * 3 < angle <= math.pi / 4 * 7:
        state[18] += 1 / util.distance(game.player_agent.position, stuff.position)
      if math.pi / 4 * 7 < angle <= math.pi * 2:
        state[19] += 1 / util.distance(game.player_agent.position, stuff.position)
    if weight > 0:
      state[4] = round(state[4] / weight, 2)
      state[5] = round(state[5] / weight, 2)
      state[6] = round(state[6] / weight, 2)
      state[7] = round(state[7] / weight, 2)
      state[8] = round(state[8] / weight, 2)
      state[9] = round(state[9] /weight, 2)
      state[10] = round(state[10] / weight, 2)
      state[11] = round(state[11] / weight, 2)
 
 
    return np.asarray(state)
 
  def set_reward(self, game, dead, damage):
    self.reward = 0.001
    if dead:
      self.reward -= 1
    if damage:
      self.reward -= 1
    target_pos = util.dense_position(game, 5)
    # compute the distance between player_agent and the target position
    dist = util.distance(game.player_agent.position, target_pos)
    if dist < 200:
      self.reward += 1 / math.log(dist, 10) if dist > 10 else 1
    for stuff in game.map_info['stuffs']:
      dist = util.distance(game.player_agent.position, stuff.position)
      if dist < game.player_agent.radius * 2.5:
        self.reward += -1 / math.log(dist, 10) if dist > 10 else 1

    if self.stopping_step > 0 and self.reward < 0.4:
      self.reward -= self.stopping_step / 1000

    return self.reward
 
 
  def network(self, weights=None):
    model = Sequential()
    model.add(Dense(output_dim=16, activation='relu', input_dim=20))
    model.add(Dropout(0.15))
    model.add(Dense(output_dim=32, activation='relu'))
    model.add(Dropout(0.15))
    model.add(Dense(output_dim=64, activation='relu'))
    model.add(Dropout(0.15))
    model.add(Dense(output_dim=32, activation='relu'))
    model.add(Dropout(0.15))
    model.add(Dense(output_dim=16, activation='relu'))
    model.add(Dropout(0.15))
    model.add(Dense(output_dim=9, activation='softmax'))
    opt = RAdam(self.learning_rate)
    model.compile(loss='mse', optimizer=opt)
 
    if weights:
      model.load_weights(weights)
    return model
  def remember(self, state, action, reward, next_state, done, hit):
    self.memory.append((state, action, reward, next_state, done, hit))
 
  def replay_new(self, memory, number):
    if len(memory) > number:
      minibatch = random.sample(memory, number)
    else:
      minibatch = memory
  
    for state, action, reward, next_state, done, hit in minibatch:
      target = reward
      if not done:
        target = reward + self.gamma * np.amax(self.model.predict(np.array([next_state]))[0])
      target_f = self.model.predict(np.array([state]))
      target_f[0][np.argmax(action)] = target
      self.model.fit(np.array([state]), target_f, epochs=1, verbose=0)
 
  def train_short_memory(self, state, action, reward, next_state, done, hit):
    target = reward
    if not done:
      target = reward + self.gamma * np.amax(self.model.predict(next_state.reshape((1, 20)))[0])
    target_f = self.model.predict(state.reshape((1, 20)))
    target_f[0][np.argmax(action)] = target
    self.model.fit(state.reshape((1, 20)), target_f, epochs=1, verbose=0)
