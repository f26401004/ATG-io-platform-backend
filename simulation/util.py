import math
import numpy as np
import zlib, json, base64

def distance(a, b):
  return math.sqrt((a['x'] - b['x']) ** 2 + (a['y'] - b['y'])**2)

def vector(hdg, len):
  return (math.cos(hdg) * len, math.sin(hdg) * len)

def angle(player_pos, target_pos):
  diff_x = target_pos['x'] - player_pos['x']
  diff_y = target_pos['y'] - player_pos['y']
  angle = math.atan2(diff_y, diff_x)
  return angle

def angle_score(angle, player_pos, target_pos):
  diff_x = target_pos['x'] - player_pos['x']
  diff_y = target_pos['y'] - player_pos['y']
  while (angle > math.pi * 2):
    angle -= math.pi * 2
  while (angle < 0):
    angle += math.pi * 2
  target_angle = math.atan2(diff_y, diff_x)
  target_angle += math.pi * 2 if target_angle < 0 else 0
  value = angle - target_angle
  if abs(value) < 0.01:
    return 1 - abs(value)
  return abs(value) * (-1)

def dense_position(game, grid_size):
  # find the dense place
  map = np.zeros((grid_size, grid_size))
  for stuff in game.map_info['stuffs']:
    x = max(min(int(stuff.position['x'] / (game.game_width / grid_size)), grid_size - 1), 0)
    y = max(min(int(stuff.position['y'] / (game.game_height / grid_size)), grid_size - 1), 0)
    map[x][y] += 1

  target_pos = np.where(map == np.amax(map))
  target_pos = {
    'x': (target_pos[0][0] + 0.5) * (game.game_width / grid_size),
    'y': (target_pos[1][0] + 0.5) * (game.game_height / grid_size)
  }
  return target_pos

def encode(target):
  message = base64.b64encode(
    zlib.compress(
      json.dumps(target).encode('utf-8')
    )
  ).decode('ascii')
  return message
