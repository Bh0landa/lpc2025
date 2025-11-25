import math
from random import uniform

import pygame as pg

import config as C
from utils import Vec, angle_to_vec, draw_circle, draw_poly, wrap_pos
try:
    from embedded_ship_frames import FRAMES as EMBED_FRAMES
except Exception:
    EMBED_FRAMES = None


# Classes que representam os sprites do jogo
# Cada classe guarda posicao, velocidade, raio e metodos de movimento e desenho
class Bullet(pg.sprite.Sprite):
    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.r = C.BULLET_RADIUS
        try:
            self._spawn_tick = pg.time.get_ticks()
        except Exception:
            self._spawn_tick = 0
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    # Atualiza posicao e tempo de vida
    def update(self, dt: float):
        self.pos += self.vel * dt
        # Se a bala sair da tela, removê-la (não atravessar/wrap)
        if self.pos.x < 0 or self.pos.x > C.WIDTH or self.pos.y < 0 or self.pos.y > C.HEIGHT:
            self.kill()
            return
        self.rect.center = self.pos
    
    # Desenha o projétil como um pequeno retângulo alinhado com a direção
    def draw(self, surf: pg.Surface):
        if self.vel.length() > 0:
            dirv = self.vel.normalize()
        else:
            dirv = Vec(1, 0)
        perp = Vec(-dirv.y, dirv.x)
        length = 12
        width = 4
        halfL = length / 2
        halfW = width / 2
        p1 = self.pos - dirv * halfL - perp * halfW
        p2 = self.pos - dirv * halfL + perp * halfW
        p3 = self.pos + dirv * halfL + perp * halfW
        p4 = self.pos + dirv * halfL - perp * halfW
        colors = [C.WHITE, (0, 200, 255), (255, 80, 80)]
        elapsed = pg.time.get_ticks() - getattr(self, '_spawn_tick', 0)
        idx = (elapsed // 40) % len(colors)
        color = colors[idx]
        pts = [p1, p2, p3, p4]
        pg.draw.polygon(surf, color, [(int(p.x), int(p.y)) for p in pts])
class Asteroid(pg.sprite.Sprite):
    def __init__(self, pos: Vec, vel: Vec, size: str):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.size = size
        self.r = C.AST_SIZES[size]["r"]
        self.poly = self._make_poly()
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def _make_poly(self):
        steps = 12 if self.size == "L" else 10 if self.size == "M" else 8
        pts = []
        for i in range(steps):
            ang = i * (360 / steps)
            jitter = uniform(0.75, 1.2)
            r = self.r * jitter
            v = Vec(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
            pts.append(v * r)
        return pts

    def update(self, dt: float):
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        pts = [(self.pos + p) for p in self.poly]
        pg.draw.polygon(surf, C.WHITE, pts, width=1)


class Ship(pg.sprite.Sprite):
    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(0, 0)
        self.angle = -90.0
        self.cool = 0.0
        self.invuln = 0.0
        self.alive = True
        self.r = C.SHIP_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        # animation: use a timer and current frame index so stopping returns
        # immediately to the base frame
        self._anim_timer = 0.0
        self._anim_frame = 0
        self._dir = 'down'

    def control(self, keys: pg.key.ScancodeWrapper, dt: float):
        mv = Vec(0, 0)
        if keys[pg.K_w]:
            mv.y -= 1
        if keys[pg.K_s]:
            mv.y += 1
        if keys[pg.K_a]:
            mv.x -= 1
        if keys[pg.K_d]:
            mv.x += 1

        if mv.length_squared() > 0:
            mv = mv.normalize()
            self.vel = mv * C.SHIP_SPEED
            if abs(mv.x) > abs(mv.y):
                self._dir = 'left' if mv.x < 0 else 'right'
            else:
                self._dir = 'up' if mv.y < 0 else 'down'
        else:
            self.vel = Vec(0, 0)

    def fire(self) -> Bullet | None:
        if self.cool > 0:
            return None
        try:
            mx, my = pg.mouse.get_pos()
            to_mouse = Vec(mx, my) - self.pos
            dirv = to_mouse.normalize() if to_mouse.length() > 0 else Vec(1, 0)
        except Exception:
            dirv = Vec(1, 0)
        pos = self.pos + dirv * (self.r + 4)
        vel = dirv * C.BULLET_SPEED
        self.cool = C.SHIP_FIRE_RATE
        return Bullet(pos, vel)

    def hyperspace(self):
        self.pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))
        self.vel.xy = (0, 0)
        self.invuln = 1.0

    def update(self, dt: float, mouse_pos=None):
        if self.cool > 0:
            self.cool -= dt
        if self.invuln > 0:
            self.invuln -= dt
        # animation timing: when moving, advance frames at fixed rate; when
        # stopped, reset to base frame immediately
        if self.vel.length_squared() > 0:
            frame_rate = 6.0  # frames per second
            frame_duration = 1.0 / frame_rate
            self._anim_timer += dt
            if self._anim_timer >= frame_duration:
                steps = int(self._anim_timer / frame_duration)
                self._anim_timer -= steps * frame_duration
                # accumulate frame steps; modulo applied at draw time
                self._anim_frame = self._anim_frame + steps
        else:
            self._anim_timer = 0.0
            self._anim_frame = 0
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Use embedded frames if available (generated from imagens),
        # otherwise fall back to small built-in placeholder.
        # If embedded frames are color frames (dicts with 'pixels'), use them.
        # Use only embedded frames; remove the ASCII fallback per project decision.
        FRAMES = EMBED_FRAMES

        main_col = C.WHITE
        dark = (30, 30, 30)

        dir_key = getattr(self, '_dir', 'down')
        # FRAMES is expected to be EMBED_FRAMES. Be safe if it's None.
        if FRAMES:
            frames_for_dir = FRAMES.get(dir_key, FRAMES.get('down', []))
        else:
            frames_for_dir = []

        # If ship is not moving, prefer an explicit 'base' frame if present.
        idle_frame = None
        if EMBED_FRAMES is not None:
            # direct 'base' key
            if 'base' in EMBED_FRAMES and EMBED_FRAMES['base']:
                idle_frame = EMBED_FRAMES['base'][0]
            else:
                # search all embedded frames for a source named 'base' (case-insensitive)
                for k, lst in EMBED_FRAMES.items():
                    for fr in lst:
                        name = fr.get('name', '').lower() if isinstance(fr, dict) else ''
                        if 'base' in name:
                            idle_frame = fr
                            break
                    if idle_frame is not None:
                        break

        # choose frame: if stopped and idle_frame found, use it; otherwise animate
        if self.vel.length_squared() == 0 and idle_frame is not None:
            frame = idle_frame
        else:
            # pick frame index from the integer anim counter (wrap by available frames)
            if isinstance(frames_for_dir, list) and len(frames_for_dir) > 0:
                frame_idx = int(self._anim_frame) % len(frames_for_dir)
            else:
                frame_idx = 0
            frame = frames_for_dir[frame_idx]

        # If frame is a dict with 'pixels', render color pixels preserving size
        if isinstance(frame, dict) and 'pixels' in frame:
            w = int(frame['w'])
            h = int(frame['h'])
            pixels = frame['pixels']
            scale = int(getattr(C, 'SHIP_PIXEL_SCALE', 1))
            scale = max(1, scale)
            spr = pg.Surface((w * scale, h * scale), pg.SRCALPHA)
            for y, row in enumerate(pixels):
                for x, col in enumerate(row):
                    r, g, b, a = col
                    if a == 0:
                        continue
                    rect = pg.Rect(x * scale, y * scale, scale, scale)
                    # draw with alpha-supporting surface
                    pg.draw.rect(spr, (r, g, b, a), rect)
            rect = spr.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            surf.blit(spr, rect)
        else:
            # Fallback: ascii-style frames (legacy)
            GRID = 8
            pixel_size = int(getattr(C, 'SHIP_PIXEL_SCALE', 3))
            pixel_size = max(1, pixel_size)
            w = GRID * pixel_size
            h = GRID * pixel_size
            spr = pg.Surface((w, h), pg.SRCALPHA)
            for y, row in enumerate(frame):
                for x, ch in enumerate(row):
                    if ch == '1':
                        rect = pg.Rect(x * pixel_size, y * pixel_size, pixel_size, pixel_size)
                        pg.draw.rect(spr, main_col, rect)
                    elif ch == '2':
                        rect = pg.Rect(x * pixel_size, y * pixel_size, pixel_size, pixel_size)
                        pg.draw.rect(spr, dark, rect)
            rect = spr.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            surf.blit(spr, rect)

        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            draw_circle(surf, self.pos, self.r + 6)


class UFO(pg.sprite.Sprite):
    def __init__(self, pos: Vec, small: bool):
        super().__init__()
        self.pos = Vec(pos)
        self.small = small
        self.r = C.UFO_SMALL["r"] if small else C.UFO_BIG["r"]
        self.speed = C.UFO_SPEED
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.dir = Vec(1, 0) if uniform(0, 1) < 0.5 else Vec(-1, 0)
        # cooldown para disparo do UFO
        self.fire_cool = 0.0
        self.fire_rate = 2.5 if small else 4.0
        # fator de mira do UFO
        self.aim = C.UFO_SMALL["aim"] if small else C.UFO_BIG["aim"]

    def update(self, dt: float):
        self.pos += self.dir * self.speed * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    # Desenha o corpo do UFO como elipse
    def draw(self, surf: pg.Surface):
        w, h = self.r * 2, self.r
        rect = pg.Rect(0, 0, w, h)
        rect.center = self.pos
        pg.draw.ellipse(surf, C.WHITE, rect, width=1)
        cup = pg.Rect(0, 0, w * 0.5, h * 0.7)
        cup.center = (self.pos.x, self.pos.y - h * 0.3)
        pg.draw.ellipse(surf, C.WHITE, cup, width=1)


class UFObullet(pg.sprite.Sprite):
    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.r = C.BULLET_RADIUS
        try:
            self._spawn_tick = pg.time.get_ticks()
        except Exception:
            self._spawn_tick = 0
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        self.pos += self.vel * dt
        # Se o projétil inimigo sair da tela, removê-lo
        if self.pos.x < 0 or self.pos.x > C.WIDTH or self.pos.y < 0 or self.pos.y > C.HEIGHT:
            self.kill()
            return
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Desenha retângulo piscante para projétil inimigo (similar ao do jogador)
        if self.vel.length() > 0:
            dirv = self.vel.normalize()
        else:
            dirv = Vec(1, 0)
        perp = Vec(-dirv.y, dirv.x)
        length = 10
        width = 3
        halfL = length / 2
        halfW = width / 2
        p1 = self.pos - dirv * halfL - perp * halfW
        p2 = self.pos - dirv * halfL + perp * halfW
        p3 = self.pos + dirv * halfL + perp * halfW
        p4 = self.pos + dirv * halfL - perp * halfW
        colors = [C.WHITE, (0, 200, 255), (255, 80, 80)]
        # piscar por projétil: calcula índice baseado no tempo desde o spawn
        elapsed = pg.time.get_ticks() - getattr(self, '_spawn_tick', 0)
        idx = (elapsed // 40) % len(colors)
        color = colors[idx]
        pts = [p1, p2, p3, p4]
        pg.draw.polygon(surf, color, [(int(p.x), int(p.y)) for p in pts])