import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pygame as pg
pg.init()

from systems import World
from utils import Vec
import config as C
from sprites import Barrel
from random import uniform

w = World()
# create TNT barrel at center
bar = Barrel(C.WIDTH/2, C.HEIGHT/2)
bar.pos = Vec(C.WIDTH/2, C.HEIGHT/2)
bar.landed = True
bar.kind = 'tnt'
bar.hp = 0
bar.exploded = True
bar.explosion_timer = float(getattr(C, 'BARREL_TNT_EXPLOSION_TIME', 0.28))
bar.explosion_radius = float(getattr(C, 'BARREL_TNT_EXPLOSION_RADIUS', 80))
w.all_sprites.add(bar)
w.barrels.add(bar)

# spawn an asteroid within explosion radius
from sprites import Asteroid
ast = Asteroid(Vec(C.WIDTH/2 + 10, C.HEIGHT/2), Vec(0,0), 'S')
w.asteroids.add(ast)
w.all_sprites.add(ast)

print('Before: ast alive?', ast in w.asteroids)
# ensure safe disabled
w.safe = 0.0
# run collisions to process explosion
w.handle_collisions()
print('After: ast alive?', ast in w.asteroids)

pg.quit()
