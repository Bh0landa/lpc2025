import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pygame as pg
pg.init()

from systems import World
from utils import Vec
import config as C

w = World()
# place ship just above center and record prev pos
w.ship.pos = Vec(C.WIDTH/2, C.HEIGHT/2 - 5)
w.ship._prev_pos = Vec(C.WIDTH/2, C.HEIGHT/2 - 10)
# spawn barrel at center (target_y already same)
from sprites import Barrel
bar = Barrel(C.WIDTH/2, C.HEIGHT/2)
bar.pos = Vec(C.WIDTH/2, C.HEIGHT/2)
bar.landed = True
w.all_sprites.add(bar)
w.barrels.add(bar)

print('Before collision: ship pos', w.ship.pos, 'prev', getattr(w.ship, '_prev_pos', None))
# run collision handler
# debug: print radii and distance
from math import hypot
dist = (w.ship.pos - bar.pos).length()
print('ship.r, bar.r, dist =', w.ship.r, bar.r, dist)
w.safe = 0.0
w.handle_collisions()
print('After collision: ship pos', w.ship.pos)

pg.quit()
