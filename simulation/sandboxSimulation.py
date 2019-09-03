def warn(*args, **kwargs):
    pass
import warnings
import os
import signal
warnings.warn = warn
warnings.simplefilter(action='ignore', category=FutureWarning)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


import sys
sys.path.append('..') 

import numpy as np
import random
import util
import math
import subprocess
from DQN import DQNMoveAgent
from keras.utils import to_categorical

import threading
import time
import json
from objects import Player
from objects import Stuff
from objects import Bullet
import redis



class Game:
  def __init__(self, game_width, game_height, agent, user_agent):
    # set the game field
    self.game_width = game_width
    self.game_height = game_height
    self.field = {
      'width': game_width,
      'height': game_height
    }
    self.redisClient = redis.Redis(host='127.0.0.1', port=6379, db=0)


    self.agent = agent
    self.user_agent = user_agent

    # generate the player instance
    self.player_agent = Player(random.randint(50, self.game_width - 50), random.randint(50, self.game_height - 50))
    self.player_user = Player(random.randint(50, self.game_width - 50), random.randint(50, self.game_height - 50))
    flag = True
    x = random.randint(50, self.game_width - 50)
    y = random.randint(50, self.game_height - 50)
    while(flag):
      flag = False
      x = random.randint(50, self.game_width - 50)
      y = random.randint(50, self.game_height - 50)
      position = {
        'x': x,
        'y': y
      }
      if (util.distance(self.player_agent.position, position) < self.player_user.radius + self.player_agent.radius):
        flag = True
    self.player_user.position['x'] = x
    self.player_user.position['y'] = y
    # initialize the map infomation
    self.map_info = {
      'stuffs': [],
      'bullets': []
    }

    # initialize the basic infomation of the game
    self.score = 0
    self.timeout = False

    # initialize the agent action
    self.initialize(agent)

  def initialize(self, agent):
    # random generate stuff
    for i in range(100):
      x = random.randint(50, self.game_width - 50)
      y = random.randint(50, self.game_height - 50)
      # check collision
      flag = True
      while flag:
        flag = False
        x = random.randint(50, self.game_width - 50)
        y = random.randint(50, self.game_height - 50)
        position = {
          'x': x,
          'y': y
        }
        if (util.distance(self.player_agent.position, position) < 15 + self.player_agent.radius):
          flag = True
        if (util.distance(self.player_user.position, position) < 15 + self.player_user.radius):
          flag = True
        for stuff in self.map_info['stuffs']:
          if (util.distance(stuff.position, position) < stuff.radius * 2):
            flag = True
      stuff = Stuff(x, y)
      self.map_info['stuffs'].append(stuff)

    # get the old state of the agent
    old_state = agent.get_state(self)
    # initialize the action with all zero
    action = [0, 0, 0, 0, 0, 0] # shoot, angle, move up, move down, move left, move right
    # let player do the action
    self.player_agent.do_move_action(self, action)
    # get the new state after do the action
    new_state = agent.get_state(self)
    # get the reward from the current status
    reward = agent.set_reward(self, self.player_agent.attr['hp'] > 0, self.player_agent.hit)
    # remember the status and replay with the memory
    agent.remember(old_state, action, reward, new_state, self.player_agent.attr['hp'] > 0, self.player_agent.hit)

    
  def deal_with_collisions(self):
    collisions = []
    player_agent = self.player_agent
    player_user = self.player_user
    player_agent.hit = False
    player_user.hit = False
    # (player, stuff), (player, bullet), (player, diep)
    # (stuff, bullet), (stuff, stuff), (stuff, diep)
    # (bullet, bullet), (bullet, diep)

    
    for stuff in self.map_info['stuffs']:
      stuff.hit = False
      # detect player collide with stuff
      if (util.distance(player_agent.position, stuff.position) < player_agent.radius + stuff.radius):
        player_agent.hit = stuff.hit = True
        if not (((player_agent, stuff) in collisions) or ((stuff, player_agent) in collisions)):
          collisions.append((player_agent, stuff))
      if (util.distance(player_user.position, stuff.position) < player_user.radius + stuff.radius):
        player_user.hit = stuff.hit = True
        if not (((player_user, stuff) in collisions) or ((stuff, player_user) in collisions)):
          collisions.append((player_user, stuff))
      # detect stuff collide with stuff
      for stuff2 in self.map_info['stuffs']:
        if (stuff == stuff2):
          continue
        if (util.distance(stuff.position, stuff2.position) < stuff.radius + stuff2.radius):
          stuff.hit = stuff2.hit = True
          if not (((stuff, stuff2) in collisions) or ((stuff2, stuff) in collisions)):
            collisions.append((stuff, stuff2))
    # detect player collide with bullet
    for bullet in self.map_info['bullets']:
      bullet.hit = False
      if (bullet.owner == player_agent.id):
        continue
      if (util.distance(player_agent.position, bullet.position) < player_agent.radius + bullet.radius):
        player_agent.hit = bullet.hit = True
        if not (((player_agent, bullet) in collisions) or ((bullet, player_agent) in collisions)):
          collisions.append((player_agent, bullet))
    for bullet in self.map_info['bullets']:
      if (bullet.owner == player_user.id):
        continue
      if (util.distance(player_user.position, bullet.position) < player_user.radius + bullet.radius):
        player_user.hit = bullet.hit = True
        if not (((player_user, bullet) in collisions) or ((bullet, player_user) in collisions)):
          collisions.append((player_user, bullet))
    
    for bullet in self.map_info['bullets']:
      # detect stuff collide with bullet
      for stuff in self.map_info['stuffs']:
        if (util.distance(bullet.position, stuff.position) < bullet.radius + stuff.radius):
          bullet.hit = stuff.hit = True
          if not (((stuff, bullet) in collisions) or ((bullet, stuff) in collisions)):
            collisions.append((stuff, bullet))
      # detect bullet collide with bullet
      for bullet2 in self.map_info['bullets']:
        if (bullet == bullet2):
          continue
        if (util.distance(bullet.position, bullet2.position) < bullet.radius + bullet2.radius):
          bullet.hit = bullet2.hit = True
          if not (((bullet, bullet2) in collisions) or ((bullet2, bullet) in collisions)):
            collisions.append((bullet, bullet2))
    # deal with all collision pair
    for pair in collisions:
      # physical object collision 
      self.object_collision(pair)
      # call the collide_with function
      pair[0].collide_with(pair[1])
      pair[1].collide_with(pair[0])
    for stuff in self.map_info['stuffs']:
      if stuff.attr['hp'] <= 0:
        self.map_info['stuffs'].remove(stuff)
    for bullet in self.map_info['bullets']:
      if bullet.attr['hp'] <= 0:
        self.map_info['bullets'].remove(bullet)

  def object_collision(self, pair):
    copy = pair[0].velocity.copy()
    pair[0].velocity['x'] = pair[1].velocity['x']
    pair[0].velocity['y'] = pair[1].velocity['y']
   
    pair[1].velocity['x'] = copy['x']
    pair[1].velocity['y'] = copy['y']

    copy = pair[0].acceleration.copy()
    pair[0].acceleration['up'] = pair[1].acceleration['up']
    pair[0].acceleration['down'] = pair[1].acceleration['down']
    pair[0].acceleration['left'] = pair[1].acceleration['left']
    pair[0].acceleration['right'] = pair[1].acceleration['right']

    pair[1].acceleration['up'] = copy['up']
    pair[1].acceleration['down'] = copy['down']
    pair[1].acceleration['left'] = copy['left']
    pair[1].acceleration['right'] = copy['right']

  def agent_move(self):
    final_action = np.zeros(8)
    old_state = self.agent.get_state(self)
    prediction = self.agent.model.predict(old_state.reshape(1, 20))
    final_action = to_categorical(np.argmax(prediction[0]), num_classes=9)
        
    self.player_agent.do_move_action(self, final_action)
    new_state = self.agent.get_state(self)
    reward = self.agent.set_reward(self, self.player_agent.attr['hp'] <= 0, self.player_agent.hit)
    self.agent.train_short_memory(old_state, final_action, reward, new_state, self.player_agent.attr['hp'] <= 0, self.player_agent.hit)
    self.agent.remember(old_state, final_action, reward, new_state, self.player_agent.attr['hp'] <= 0, self.player_agent.hit)
    
    target = None
    angle = -1
    # find the closest stuff and shoot
    for stuff in self.map_info['stuffs']:
      dist = util.distance(self.player_agent.position, stuff.position)
      if target:
        if dist < 200 and util.distance(self.player_agent.position, target.position) > dist:
          angle = util.angle(self.player_agent.position, stuff.position)
          target = stuff
      else:
        if dist < 200:
          angle = util.angle(self.player_agent.position, stuff.position)
          target = stuff
    if util.distance(self.player_agent.position, self.player_user.position) < 200:
      angle = util.angle(self.player_agent.position, self.player_user.position)
      target = self.player_user
    if target:
      self.player_agent.do_shoot_action(self, [1, angle])

  def user_move(self):
    # refactor the game information
    # transform the map information to string
    data = ''
    for stuff in self.map_info['stuffs']:
      x = int(stuff.position['x'])
      y = int(stuff.position['y'])
      data += 'S ' if stuff.attr['hp'] > 50 else 's '
      data += str(x) + ' ' + str(y) + '\n'
    data += 'O ' + str(int(self.player_agent.position['x'])) + ' ' + str(int(self.player_agent.position['y'])) + '\n'
    data += 'P ' + str(int(self.player_user.position['x'])) + ' ' + str(int(self.player_user.position['y'])) + '\n'

    for bullet in self.map_info['bullets']:
      x = int(bullet.position['x'])
      y = int(bullet.position['y'])
      data += 'B ' if bullet.owner == self.player_user.id else 'b '
      data += str(x) + ' ' + str(y) + '\n'
    
    data += 'end\n'
    self.user_agent.stdin.write(data)
    # get the action from the user program
    action = ''
    
    output = self.user_agent.stdout.readline()
    action = []
    number = ''
    for i in output:
      if i == ' ':
        action.append(float(number))
        number = ''
        continue
      number += i
    action.append(float(number))
    # do the action
    if (action[2] == 1 and action[3] == 0 and action[4] == 0 and action[5] == 0):
      self.player_user.do_move_action(self, np.array([0, 1, 0, 0, 0, 0, 0, 0, 0]))
    elif (action[2] == 0 and action[3] == 1 and action[4] == 0 and action[5] == 0):
      self.player_user.do_move_action(self, np.array([0, 0, 1, 0, 0, 0, 0, 0, 0]))
    elif (action[2] == 0 and action[3] == 0 and action[4] == 1 and action[5] == 0):
      self.player_user.do_move_action(self, np.array([0, 0, 0, 1, 0, 0, 0, 0, 0]))
    elif (action[2] == 0 and action[3] == 0 and action[4] == 0 and action[5] == 1):
      self.player_user.do_move_action(self, np.array([0, 0, 0, 0, 1, 0, 0, 0, 0]))
    elif (action[2] == 1 and action[3] == 0 and action[4] == 1 and action[5] == 0):
      self.player_user.do_move_action(self, np.array([0, 0, 0, 0, 0, 1, 0, 0, 0]))
    elif (action[2] == 1 and action[3] == 0 and action[4] == 0 and action[5] == 1):
      self.player_user.do_move_action(self, np.array([0, 0, 0, 0, 0, 0, 1, 0, 0]))
    elif (action[2] == 0 and action[3] == 1 and action[4] == 1 and action[5] == 0):
      self.player_user.do_move_action(self, np.array([0, 0, 0, 0, 0, 0, 0, 1, 0]))
    elif (action[2] == 0 and action[3] == 1 and action[4] == 0 and action[5] == 1):
      self.player_user.do_move_action(self, np.array([0, 0, 0, 0, 0, 0, 0, 0, 1]))
    else:
      self.player_user.do_move_action(self, np.array([1, 0, 0, 0, 0, 0, 0, 0, 0]))
    self.player_user.do_shoot_action(self, action[0:2])
    

  def update(self):
    start = time.time()
    # update all object attribute
    self.player_agent.update()
    self.player_user.update()

    for stuff in self.map_info['stuffs']:
      stuff.update()
    for bullet in self.map_info['bullets']:
      bullet.update()
    # detect collisions
    self.deal_with_collisions()
    
    if not (self.player_user.attr['hp'] <= 0 or self.player_agent.attr['hp'] <= 0 or self.timeout):
      self.agent_move()
      self.user_move()
      # dump the message
      message = {
        'playerUser': {
          'id': str(self.player_user.id),
          'x': int(self.player_user.position['x']),
          'y': int(self.player_user.position['y']),
          'radius': self.player_user.radius,
          'hp': int(self.player_user.attr['hp'])
        },
        'playerOpponent': {
          'id': str(self.player_agent.id),
          'x': int(self.player_agent.position['x']),
          'y': int(self.player_agent.position['y']),
          'radius': self.player_agent.radius,
          'hp': int(self.player_agent.attr['hp'])
        },
        'stuffs': {},
        'bullets': {}
      }
      for stuff in self.map_info['stuffs']:
        message['stuffs'][str(stuff.id)] = {
          'x': int(stuff.position['x']),
          'y': int(stuff.position['y']),
          'radius': stuff.radius,
          'hp': int(stuff.attr['hp'])
        }
      for bullet in self.map_info['bullets']:
        message['bullets'][str(bullet.id)] = {
          'x': int(bullet.position['x']),
          'y': int(bullet.position['y']),
          'radius': bullet.radius
        }
      
      message = util.encode(message)
      # publish the message
      self.redisClient.publish(
        'worker' + sys.argv[2] + 'simulation',
        message
      )
      
    else:
      status = False
      elapsed_time = time.time() - start_time
      if (self.player_agent.attr['hp'] <= 0 or self.player_user.attr['hp'] > self.player_agent.attr['hp']):
        status = True
      elif (self.player_agent.score < self.player_user.score):
        status = True
      result = {
        'score': self.player_user.score,
        'result': status,
        'elapsedTime': elapsed_time * 1000
      }
      message = util.encode(result)
      # publish the message
      self.redisClient.publish(
        'worker' + sys.argv[2] + 'simulation',
        message
      )
      self.timeout = True
  


def start():
  # initialize the agent instance
  agent = DQNMoveAgent()
  # initialize the user code
  user_agent = subprocess.Popen(['./bins/' + sys.argv[1]],
    shell=True,
    stdin=subprocess.PIPE, 
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT,
    bufsize=1,
    universal_newlines=True)
  

  # initialize the network
  game = Game(1600, 900, agent, user_agent)
  # reward counter
  current_reward = 0

  def timeout ():
    elapsed_time = time.time() - start_time if time.time() - start_time < 60 else 60
    status = False
    if (self.player_agent.attr['hp'] <= 0 or self.player_user.attr['hp'] > self.player_agent.attr['hp']):
      status = True
    elif (self.player_agent.score < self.player_user.score):
      status = True
    result = {
      'score': game.player_user.score,
      'result': status,
      'elapsedTime': elapsed_time * 1000
    }
    message = util.encode(result)
    # publish the message
    game.redisClient.publish(
      'worker' + sys.argv[2] + 'simulation',
      message
    )
    game.timeout = True
  
  # config game timeout
  timeoutCounter = threading.Timer(60, timeout)
  timeoutCounter.start()

  while(not game.timeout):
    game.update()
    
  
    
  agent.replay_new(agent.memory, 1000)
  agent.model.save_weights('./simulation/move_weights.hdf5')
  user_agent.kill()

# record the start time
start_time = time.time()

start()