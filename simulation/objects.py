def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
warnings.simplefilter(action='ignore', category=FutureWarning)

import random
import json
import uuid
import math
import numpy as np

friction = 0.97

class GameObject(object):
  def __init__(self, x, y):
    self.id = uuid.uuid4()
    self.radius = 15
    self.hit = False
    self.velocity = {
      'x': 0.0,
      'y': 0.0
    }
    self.position = {
      'x': x,
      'y': y
    }
    self.acceleration = {
      'up': 0.0,
      'down': 0.0,
      'left': 0.0,
      'right': 0.0
    }
    self.move_direction = {
      'up': False,
      'down': False,
      'left': False,
      'right': False
    }

  def move(self, type_str):
    self.move_direction[type_str] = True
  
  def update(self):
    if (self.move_direction['up']):
      self.acceleration['up'] = 10
    if (self.move_direction['down']):
      self.acceleration['down'] = 10
    if (self.move_direction['left']):
      self.acceleration['left'] = 10
    if (self.move_direction['right']):
      self.acceleration['right'] = 10

    self.velocity['x'] = (self.acceleration['down'] - self.acceleration['up']) * friction
    self.velocity['y'] = (self.acceleration['right'] - self.acceleration['left']) * friction

    self.position['x'] = min(max(self.position['x'] + self.velocity['x'], 0), 1600)
    self.position['y'] = min(max(self.position['y'] + self.velocity['y'], 0), 900)

  def collide_with(self, collider):
    pass

class Player(GameObject):
  def __init__(self, x, y):
    GameObject.__init__(self, x, y)
    self.radius = 15
    self.score = 0
    self.attr = {
      'hp': 100,
      'maxhp': 100,
      'level': 1,
      'exp': 0,
      'shoot_cd': 0
    }
    self.status = {
      'maxhp': 1,
      'hp_regeneration': 1,
      'move_speed': 1,
      'bullet_speed': 1,
      'bullet_penetration': 1,
      'bullet_reload': 1,
      'bullet_damage': 1,
      'body_damage': 1
    }
    self.shoot_status = {
      'fire': False,
      'angle': 0,
      'cd': 0
    }

  def do_move_action(self, game, action):
    self.move_direction = {
      'up': False,
      'down': False,
      'left': False,
      'right': False
    }
    type_num = np.argwhere(action == 1)
    if type_num == 1:
      self.move_direction['up'] = True
    elif type_num == 2:
      self.move_direction['down'] = True
    elif type_num == 3:
      self.move_direction['left'] = True
    elif type_num == 4:
      self.move_direction['right'] = True
    elif type_num == 5:
      self.move_direction['up'] = True
      self.move_direction['left'] = True
    elif type_num == 6:
      self.move_direction['up'] = True
      self.move_direction['right'] = True
    elif type_num == 7:
      self.move_direction['down'] = True
      self.move_direction['left'] = True
    elif type_num == 8:
      self.move_direction['down'] = True
      self.move_direction['right'] = True

  def do_shoot_action(self, game, action):
    self.shoot_status['fire'] = False
    if action[0] == 1 and self.shoot_status['cd'] <= 0:
      self.shoot_status['fire'] = True
      self.shoot_status['angle'] = action[1]
      existence = (self.status['bullet_penetration'] - 1) * 5 + 20
      bullet = Bullet(self.position['x'], self.position['y'], existence, self.status['bullet_damage'], {
        'x': math.cos(action[1]) * (10 + self.status['bullet_speed']),
        'y': math.sin(action[1]) * (10 + self.status['bullet_speed'])
      }, self.id)
      game.map_info['bullets'].append(bullet)
      self.shoot_status['cd'] = 50 * math.log(self.status['bullet_reload'] + 1, 10)
  
  def update(self):
    self.shoot_status['cd'] -= 0 if self.shoot_status['cd'] <= 0 else 1
    self.acceleration = {
      'up': 0,
      'down': 0,
      'left': 0,
      'right': 0
    }
    if (self.move_direction['up']):
      self.acceleration['up'] = 10
    if (self.move_direction['down']):
      self.acceleration['down'] = 10
    if (self.move_direction['left']):
      self.acceleration['left'] = 10
    if (self.move_direction['right']):
      self.acceleration['right'] = 10
    self.acceleration['up'] = self.acceleration['up'] * friction
    self.acceleration['down'] = self.acceleration['down'] * friction
    self.acceleration['left'] = self.acceleration['left'] * friction
    self.acceleration['right'] = self.acceleration['right'] * friction

    if self.acceleration['down'] - self.acceleration['up'] > 0:
      self.velocity['y'] = min((self.acceleration['down'] - self.acceleration['up']) * friction, math.sqrt(self.status['move_speed'] + 5))
    else:
      self.velocity['y'] = max((self.acceleration['down'] - self.acceleration['up']) * friction, math.sqrt(self.status['move_speed'] + 5) * (-1))
    if self.acceleration['right'] - self.acceleration['left'] > 0:
      self.velocity['x'] = min((self.acceleration['right'] - self.acceleration['left']) * friction, math.sqrt(self.status['move_speed'] + 5))
    else:
      self.velocity['x'] = max((self.acceleration['right'] - self.acceleration['left']) * friction, math.sqrt(self.status['move_speed'] + 5)* (-1))
    
    self.position['x'] = min(max(self.position['x'] + self.velocity['x'], 0), 1600)
    self.position['y'] = min(max(self.position['y'] + self.velocity['y'], 0), 900)
    self.shoot_status['cd'] -= 0 if self.shoot_status['cd'] <= 0 else 1
    self.attr['hp'] += math.log(self.status['hp_regeneration'] + 1, 10) if self.attr['hp'] <= self.attr['maxhp'] else 0
    self.attr['hp'] = max(min(self.attr['hp'], self.attr['maxhp']), 0)

  def collide_with(self, collider):
    self.attr['hp'] -= collider.attr['body_damage'] * 5
    self.attr['hp'] = max(min(self.attr['hp'], self.attr['maxhp']), 0)


class Stuff(GameObject):
  def __init__(self, x, y):
    GameObject.__init__(self, x, y)
    self.radius = 15

    # reader = open('stuffType.json', 'r')
    # stuff_type = json.loads(reader.read())
    # type_number = 1#random.randint(1, 5)
    self.attr = {
      'hp': 100, #stuff_type[str(type_number)]['HP'],
      'exp': 10, #stuff_type[str(type_number)]['EXP'],
      'body_damage': 1 #stuff_type[str(type_number)]['BodyDamage']
    }
  
  def update(self):
    self.acceleration['up'] = self.acceleration['up'] * friction
    self.acceleration['down'] = self.acceleration['down'] * friction
    self.acceleration['left'] = self.acceleration['left'] * friction
    self.acceleration['right'] = self.acceleration['right'] * friction

    self.velocity['x'] = (self.velocity['x']) * friction
    self.velocity['y'] = (self.velocity['y']) * friction

    self.position['x'] = min(max(self.position['x'] + self.velocity['x'], 0), 1600)
    self.position['y'] = min(max(self.position['y'] + self.velocity['y'], 0), 900)

  def collide_with(self, collider):
    if (type(collider) == Player):
      self.attr['hp'] -= math.log(collider.status['body_damage'] + 1)
      if (self.attr['hp'] <= 0):
        collider.score += 1
        game.map_info['stuffs'].remove(self)
    elif (type(collider) == Bullet):
      self.attr['hp'] -= collider.attr['body_damage'] * 5
    else:
      self.attr['hp'] -= collider.attr['body_damage'] * 5

    self.attr['hp'] = max(min(self.attr['hp'], 100), 0)
    
      

class Bullet(GameObject):
  def __init__(self, x, y, hp, damage, velocity, owner):
    GameObject.__init__(self, x, y)
    self.radius = 5
    self.owner = owner
    self.velocity = velocity
    self.acceleration = {
      'up': math.log(velocity['y'] * -1) if velocity['y'] < 0 else 0,
      'down': math.log(velocity['y']) if velocity['y'] > 0 else 0,
      'left': math.log(velocity['x'] * -1) if velocity['x'] < 0 else 0,
      'right': math.log(velocity['x']) if velocity['x'] > 0 else 0,
    }

    self.attr = {
      'hp': hp,
      'body_damage': damage
    }
  
  def update(self):
    self.attr['hp'] -= 1

    self.position['x'] = self.position['x'] + self.velocity['x']
    self.position['y'] = self.position['y'] + self.velocity['y']

  def collide_with(self, collider):
    self.attr['hp'] = 0
    
