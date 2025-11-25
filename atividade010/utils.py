import math
from random import random, uniform
from typing import Iterable, Tuple

import pygame as pg

import config as C

# Tipo util para vetores 2D
Vec = pg.math.Vector2


def wrap_pos(pos: Vec) -> Vec:
    # Envolve a posicao nas bordas da tela
    return Vec(pos.x % C.WIDTH, pos.y % C.HEIGHT)


def angle_to_vec(deg: float) -> Vec:
    # Converte angulo em graus para um vetor unitario
    rad = math.radians(deg)
    return Vec(math.cos(rad), math.sin(rad))


def rand_unit_vec() -> Vec:
    # Retorna um vetor unitario aleatorio
    a = uniform(0, math.tau)
    return Vec(math.cos(a), math.sin(a))


def rand_edge_pos() -> Vec:
    # Retorna uma posicao aleatoria numa das bordas da tela
    if random() < 0.5:
        x = uniform(0, C.WIDTH)
        y = 0 if random() < 0.5 else C.HEIGHT
    else:
        x = 0 if random() < 0.5 else C.WIDTH
        y = uniform(0, C.HEIGHT)
    return Vec(x, y)


def draw_poly(surface: pg.Surface, pts: Iterable[Tuple[int, int]]):
    # Desenha um poligono com a cor padrao
    pg.draw.polygon(surface, C.WHITE, list(pts), width=1)


def draw_circle(surface: pg.Surface, pos: Vec, r: int):
    # Desenha um circulo contornado
    pg.draw.circle(surface, C.WHITE, pos, r, width=1)


def text(surface: pg.Surface, font: pg.font.Font, s: str, x: int, y: int):
    # Renderiza e desenha texto na superficie
    surf = font.render(s, True, C.WHITE)
    rect = surf.get_rect(topleft=(x, y))
    surface.blit(surf, rect)