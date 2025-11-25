import math
from random import uniform

import pygame as pg

import config as C
from sprites import Asteroid, Ship, UFO
from utils import Vec, rand_edge_pos, rand_unit_vec
from sprites import UFObullet
import sounds


# Mundo do jogo que gere entidades, pontuacao e logica global
class World:

    def __init__(self):
        # Cria a nave, grupos de sprites e variaveis de jogo
        self.ship = Ship(Vec(C.WIDTH / 2, C.HEIGHT / 2))
        self.bullets = pg.sprite.Group()
        self.ufo_bullets = pg.sprite.Group()
        self.asteroids = pg.sprite.Group()
        self.ufos = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group(self.ship)
        self.score = 0
        self.lives = C.START_LIVES
        self.wave = 0
        self.wave_cool = C.WAVE_DELAY
        self.safe = C.SAFE_SPAWN_TIME
        self.ufo_timer = C.UFO_SPAWN_EVERY

    # Inicia uma nova onda com asteroides nas bordas
    def start_wave(self):
        self.wave += 1
        count = 3 + self.wave
        for _ in range(count):
            pos = rand_edge_pos()
            while (pos - self.ship.pos).length() < 150:
                pos = rand_edge_pos()
            ang = uniform(0, math.tau)
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX)
            vel = Vec(math.cos(ang), math.sin(ang)) * speed
            self.spawn_asteroid(pos, vel, "L")

    def spawn_asteroid(self, pos: Vec, vel: Vec, size: str):
        # Cria e adiciona um asteroide ao jogo
        a = Asteroid(pos, vel, size)
        self.asteroids.add(a)
        self.all_sprites.add(a)

    def spawn_ufo(self):
        # Cria um UFO pequeno ou grande em uma das bordas
        small = uniform(0, 1) < 0.5
        y = uniform(0, C.HEIGHT)
        x = 0 if uniform(0, 1) < 0.5 else C.WIDTH
        ufo = UFO(Vec(x, y), small)
        # Ajusta direcao inicial para UFOs pequenos apontarem ao jogador
        if small:
            to_player = (self.ship.pos - ufo.pos)
            if to_player.length() > 0:
                to_player = to_player.normalize()
            ufo.dir = (ufo.dir * (1 - ufo.aim) + to_player * ufo.aim).normalize()
        else:
            ufo.dir = Vec(1, 0) if x == 0 else Vec(-1, 0)

        sounds.play_ufo_spawn()
        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

    def try_fire(self):
        # Tenta atirar a partir da nave do jogador
        # (removido limite por número de balas ativas; o cooldown em Ship.fire controla a taxa)
        b = self.ship.fire()
        if b:
            self.bullets.add(b)
            self.all_sprites.add(b)
            try:
                sounds.play_shot()
            except Exception:
                pass

    def hyperspace(self):
        # Teleporta a nave e aplica penalidade de pontos
        self.ship.hyperspace()
        self.score = max(0, self.score - C.HYPERSPACE_COST)

    def update(self, dt: float, keys):
        # Atualiza todos os sprites e timers principais
        self.all_sprites.update(dt)
        self.ufo_bullets.update(dt)
        self.ship.control(keys, dt)
        # a atualização da nave é feita por all_sprites.update

        # Timers de spawn e seguranca
        if self.safe > 0:
            self.safe -= dt
            self.ship.invuln = 0.5
        self.ufo_timer -= dt
        if self.ufo_timer <= 0:
            self.spawn_ufo()
            self.ufo_timer = C.UFO_SPAWN_EVERY

        # Logica de disparo dos UFOs
        for ufo in list(self.ufos):
            if hasattr(ufo, 'fire_cool'):
                ufo.fire_cool = max(0.0, ufo.fire_cool - dt)
                if ufo.fire_cool <= 0:
                    dir_to_player = (self.ship.pos - ufo.pos)
                    if dir_to_player.length() == 0:
                        dir_to_player = rand_unit_vec()
                    else:
                        dir_to_player = dir_to_player.normalize()
                    aim = ufo.aim if hasattr(ufo, 'aim') else 0.3
                    fire_dir = (ufo.dir * (1 - aim) + dir_to_player * aim).normalize()
                    # usa velocidade global de bala ajustada para tiros de UFO
                    vel = fire_dir * (C.BULLET_SPEED * 0.8)
                    b = UFObullet(ufo.pos + fire_dir * (ufo.r + 6), vel)
                    self.ufo_bullets.add(b)
                    self.all_sprites.add(b)
                    ufo.fire_cool = ufo.fire_rate
                    try:
                        sounds.play_ufo_shot()
                    except Exception:
                        pass

        self.handle_collisions()

        if not self.asteroids and self.wave_cool <= 0:
            self.start_wave()
            self.wave_cool = C.WAVE_DELAY
        elif not self.asteroids:
            self.wave_cool -= dt

    def handle_collisions(self):
        # Colisao entre balas do jogador e asteroides
        hits = pg.sprite.groupcollide(
            self.asteroids,
            self.bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, _ in hits.items():
            self.split_asteroid(ast)

        # Colisao entre nave do jogador e objetos se nao estiver invulneravel
        if self.ship.invuln <= 0 and self.safe <= 0:
            for ast in self.asteroids:
                if (ast.pos - self.ship.pos).length() < (ast.r + self.ship.r):
                    self.ship_die()
                    break
            for ufo in self.ufos:
                if (ufo.pos - self.ship.pos).length() < (ufo.r + self.ship.r):
                    self.ship_die()
                    break

        # Destruir ufos que colidirem com asteroides
        for ufo in list(self.ufos):
            for ast in list(self.asteroids):
                if (ast.pos - ufo.pos).length() < (ast.r + ufo.r):
                    try:
                        sounds.play_explosion()
                    except Exception:
                        pass
                    ufo.kill()
                    break

        # Colisao entre balas do jogador e ufos
        for ufo in list(self.ufos):
            for b in list(self.bullets):
                if (ufo.pos - b.pos).length() < (ufo.r + b.r):
                    score = (C.UFO_SMALL["score"] if ufo.small
                             else C.UFO_BIG["score"])
                    self.score += score
                    ufo.kill()
                    b.kill()

        # Verificar se tiros inimigos atingem a nave
        for b in list(self.ufo_bullets):
            if (b.pos - self.ship.pos).length() < (b.r + self.ship.r) and self.ship.invuln <= 0:
                b.kill()
                self.ship_die()

    def split_asteroid(self, ast: Asteroid):
        # Fragmenta asteroide e concede pontos
        self.score += C.AST_SIZES[ast.size]["score"]
        split = C.AST_SIZES[ast.size]["split"]
        pos = Vec(ast.pos)
        ast.kill()
        for s in split:
            dirv = rand_unit_vec()
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * 1.2
            self.spawn_asteroid(pos, dirv * speed, s)

    def ship_die(self):
        # Tratamento quando a nave morre
        self.lives -= 1
        self.ship.pos.xy = (C.WIDTH / 2, C.HEIGHT / 2)
        self.ship.vel.xy = (0, 0)
        self.ship.angle = -90
        self.ship.invuln = C.SAFE_SPAWN_TIME
        self.safe = C.SAFE_SPAWN_TIME
        if self.lives < 0:
            # Reinicia o mundo quando o jogador perde tudo
            self.__init__()

    def draw(self, surf: pg.Surface, font: pg.font.Font):
        # Desenha todos os sprites e o HUD
        for spr in self.all_sprites:
            spr.draw(surf)

        pg.draw.line(surf, (60, 60, 60), (0, 50), (C.WIDTH, 50), width=1)
        txt = f"SCORE {self.score:06d}   LIVES {self.lives}   WAVE {self.wave}"
        label = font.render(txt, True, C.WHITE)
        surf.blit(label, (10, 10))