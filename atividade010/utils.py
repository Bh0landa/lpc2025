# Module `utils.py` — utility helpers for vector math and simple drawing routines.
import math
from random import random, uniform
from typing import Iterable, Tuple

import pygame as pg

import config as C

# Type alias: 2D vector used throughout the game for positions and velocities.
Vec = pg.math.Vector2


def wrap_pos(pos: Vec) -> Vec:
    # Wrap a position around the screen edges (toroidal coordinates).
    return Vec(pos.x % C.WIDTH, pos.y % C.HEIGHT)


def angle_to_vec(deg: float) -> Vec:
    # Convert an angle in degrees to a unit vector pointing in that direction.
    rad = math.radians(deg)
    return Vec(math.cos(rad), math.sin(rad))


def rand_unit_vec() -> Vec:
    # Return a random unit vector (uniform direction distribution).
    a = uniform(0, math.tau)
    return Vec(math.cos(a), math.sin(a))


def rand_edge_pos() -> Vec:
    # Return a random position located on one of the screen edges.
    # Used to spawn objects that enter from the border.
    if random() < 0.5:
        x = uniform(0, C.WIDTH)
        y = 0 if random() < 0.5 else C.HEIGHT
    else:
        x = 0 if random() < 0.5 else C.WIDTH
        y = uniform(0, C.HEIGHT)
    return Vec(x, y)


def draw_poly(surface: pg.Surface, pts: Iterable[Tuple[int, int]]):
    # Draw a polygon outline using the default game color.
    pg.draw.polygon(surface, C.WHITE, list(pts), width=1)


def draw_circle(surface: pg.Surface, pos: Vec, r: int):
    # Draw a circle outline at `pos` with radius `r` using the default color.
    pg.draw.circle(surface, C.WHITE, pos, r, width=1)


def text(surface: pg.Surface, font: pg.font.Font, s: str, x: int, y: int):
    # Render `s` with `font` and blit it at (x, y) on `surface`.
    surf = font.render(s, True, C.WHITE)
    rect = surf.get_rect(topleft=(x, y))
    surface.blit(surf, rect)
