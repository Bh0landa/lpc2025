import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame as pg
pg.init()
import sys
# ensure activity010 is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from systems import World
from sprites import Barrel, Bullet
from utils import Vec
import config as C

w = World()
# spawn barrel at center
bar = Barrel(C.WIDTH/2, C.HEIGHT/2)
bar.pos = Vec(C.WIDTH/2, C.HEIGHT/2)
bar.landed = True
w.all_sprites.add(bar)
w.barrels.add(bar)

# spawn bullet exactly at barrel center
b = Bullet(bar.pos, Vec(0,0))
b.pos = Vec(bar.pos)
w.all_sprites.add(b)
w.bullets.add(b)

print('Before: barrel hp, exists in group:', getattr(bar, 'hp', None), bar in w.barrels)
# call collision handler
w.handle_collisions()
print('After: barrel hp, alive:', getattr(bar, 'hp', None), bar.alive() if hasattr(bar, 'alive') else True)
# check if barrel still in group
print('bar in group after:', bar in w.barrels)

pg.quit()
