import math
from random import uniform

import pygame as pg

import config as C
from utils import Vec, angle_to_vec, draw_circle, draw_poly, wrap_pos
try:
    from embedded_ship_frames import FRAMES as EMBED_FRAMES
except Exception:
    EMBED_FRAMES = None
try:
    from embedded_ovni_frames import FRAMES as OVNI_FRAMES
except Exception:
    OVNI_FRAMES = None
try:
    from embedded_barrel_frames import FRAMES as BARREL_FRAMES
except Exception:
    BARREL_FRAMES = None


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
        # store previous position for continuous collision checks
        try:
            self._prev_pos = Vec(self.pos)
        except Exception:
            self._prev_pos = Vec(self.pos)
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
    def get_mask(self):
        # create a small circular mask for the bullet centered on its position
        try:
            r = int(max(1, self.r))
        except Exception:
            r = 2
        w = h = r * 2
        surf = pg.Surface((w, h), pg.SRCALPHA)
        pg.draw.circle(surf, (255, 255, 255), (r, r), r)
        mask = pg.mask.from_surface(surf)
        rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        return (mask, rect)
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
        # store previous position for collision checks
        try:
            self._prev_pos = Vec(self.pos)
        except Exception:
            self._prev_pos = Vec(self.pos)
        self.pos += self.vel * dt
        # restore wrap-around behaviour so UFOs re-enter screen edges
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        pts = [(self.pos + p) for p in self.poly]
        pg.draw.polygon(surf, C.WHITE, pts, width=1)

    def get_mask(self):
        # Create filled polygon surface and mask centered at asteroid pos
        size = int(self.r * 2)
        surf = pg.Surface((size, size), pg.SRCALPHA)
        # convert poly points (vectors) into surface-local coordinates
        pts = []
        for v in self.poly:
            pts.append((int(v.x + self.r), int(v.y + self.r)))
        pg.draw.polygon(surf, (255, 255, 255), pts)
        mask = pg.mask.from_surface(surf)
        rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        return (mask, rect)


class Ship(pg.sprite.Sprite):
    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(0, 0)
        self.angle = -90.0
        self.cool = 0.0
        self.invuln = 0.0
        self.alive = True
        # Determine hit radius from embedded frames when available so
        # the collision circle matches the visual sprite size.
        scale = int(getattr(C, 'SHIP_PIXEL_SCALE', 1))
        if EMBED_FRAMES:
            # prefer an explicit 'base' frame, otherwise pick first available
            sample_frame = None
            if 'base' in EMBED_FRAMES and EMBED_FRAMES['base']:
                sample_frame = EMBED_FRAMES['base'][0]
            else:
                for lst in EMBED_FRAMES.values():
                    if lst:
                        sample_frame = lst[0]
                        break

            if isinstance(sample_frame, dict) and 'w' in sample_frame and 'h' in sample_frame:
                w = int(sample_frame['w']) * scale
                h = int(sample_frame['h']) * scale
                # Use roughly 45% of the smaller dimension as collision radius
                # to keep the hitbox inside the visible sprite.
                self.r = max(6, int(min(w, h) * 0.45))
            else:
                self.r = C.SHIP_RADIUS
        else:
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
        # store previous position to allow collision resolution that blocks movement
        try:
            self._prev_pos = Vec(self.pos)
        except Exception:
            self._prev_pos = Vec(self.pos)
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Use embedded frames if available (generated from imagens),
        # otherwise fall back to small built-in placeholder.
        # If embedded frames are color frames (dicts with 'pixels'), use them.
        # Use only embedded frames; remove the ASCII fallback per project decision.
        FRAMES = EMBED_FRAMES

        # blinking main color: cycle white -> green -> blue -> yellow
        colors_blink = [C.WHITE, (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        elapsed = pg.time.get_ticks()
        blink_idx = (elapsed // 100) % len(colors_blink)
        main_col = colors_blink[blink_idx]
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
                    # If the pixel is (near) white, replace it with the blinking main color
                    if r >= 220 and g >= 220 and b >= 220:
                        draw_color = (*main_col, a) if len(main_col) == 3 else (*main_col[:3], a)
                    else:
                        draw_color = (r, g, b, a)
                    rect = pg.Rect(x * scale, y * scale, scale, scale)
                    # draw with alpha-supporting surface
                    pg.draw.rect(spr, draw_color, rect)
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

    def get_mask(self):
        """Return (mask, rect) for the current visual frame of the ship.

        If no embedded color frame is available, returns (None, None).
        """
        # Recreate the frame selection logic from draw()
        FRAMES = EMBED_FRAMES
        dir_key = getattr(self, '_dir', 'down')
        if FRAMES:
            frames_for_dir = FRAMES.get(dir_key, FRAMES.get('down', []))
        else:
            frames_for_dir = []

        # choose frame (prefer base when idle)
        idle_frame = None
        if EMBED_FRAMES is not None:
            if 'base' in EMBED_FRAMES and EMBED_FRAMES['base']:
                idle_frame = EMBED_FRAMES['base'][0]
            else:
                for k, lst in EMBED_FRAMES.items():
                    for fr in lst:
                        name = fr.get('name', '').lower() if isinstance(fr, dict) else ''
                        if 'base' in name:
                            idle_frame = fr
                            break
                    if idle_frame is not None:
                        break

        if self.vel.length_squared() == 0 and idle_frame is not None:
            frame = idle_frame
        else:
            if isinstance(frames_for_dir, list) and len(frames_for_dir) > 0:
                frame_idx = int(self._anim_frame) % len(frames_for_dir)
            else:
                return (None, None)
            frame = frames_for_dir[frame_idx]

        if isinstance(frame, dict) and 'pixels' in frame:
            w = int(frame['w'])
            h = int(frame['h'])
            pixels = frame['pixels']
            scale = int(getattr(C, 'SHIP_PIXEL_SCALE', 1))
            scale = max(1, scale)
            # Use full rectangular mask for the ship (ignore transparency)
            spr = pg.Surface((w * scale, h * scale), pg.SRCALPHA)
            rect_full = pg.Rect(0, 0, w * scale, h * scale)
            pg.draw.rect(spr, (255, 255, 255, 255), rect_full)
            mask = pg.mask.from_surface(spr)
            rect = spr.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            return (mask, rect)

        return (None, None)


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
        # animation state for embedded ovni frames
        self._show_shot = False
        self._shot_timer = 0.0
        # Per-UFO orbit behavior: randomize around global config values
        try:
            var = float(getattr(C, 'UFO_ORBIT_VARIANCE', 0.25))
        except Exception:
            var = 0.25
        try:
            base_t = float(getattr(C, 'UFO_ORBIT_TANGENTIAL', 0.85))
            base_r = float(getattr(C, 'UFO_ORBIT_RADIAL', 0.15))
            base_turn = float(getattr(C, 'UFO_ORBIT_MAX_TURN', 3.0))
        except Exception:
            base_t, base_r, base_turn = 0.85, 0.15, 3.0
        # random +/-var multiplicative perturbation
        self.orbit_tangential = max(0.0, base_t * (1.0 + uniform(-var, var)))
        self.orbit_radial = max(0.0, base_r * (1.0 + uniform(-var, var)))
        # normalize tangential+radial so they remain meaningful weights
        s = (self.orbit_tangential + self.orbit_radial)
        if s > 0:
            self.orbit_tangential /= s
            self.orbit_radial /= s
        self.orbit_max_turn = max(0.1, base_turn * (1.0 + uniform(-var, var)))
        # If we have embedded ovni frames, derive a collision radius from
        # the visual frame size so the hitbox matches the larger sprite.
        try:
            scale = int(getattr(C, 'UFO_PIXEL_SCALE', 1))
        except Exception:
            scale = 1
        if OVNI_FRAMES:
            sample = None
            if 'base' in OVNI_FRAMES and OVNI_FRAMES['base']:
                sample = OVNI_FRAMES['base'][0]
            else:
                for lst in OVNI_FRAMES.values():
                    if lst:
                        sample = lst[0]
                        break
            if isinstance(sample, dict) and 'w' in sample and 'h' in sample:
                w = int(sample['w']) * scale
                h = int(sample['h']) * scale
                # use ~45% of the smaller dimension as collision radius
                self.r = max(self.r, max(6, int(min(w, h) * 0.45)))
                # collision radius already derived from visual size and pixel scale

    def update(self, dt: float, ship_pos: Vec = None):
        # If ship_pos is provided, attempt to orbit around the ship while
        # maintaining forward motion. Otherwise behave as before.
        if ship_pos is not None:
            to_player = (ship_pos - self.pos)
            if to_player.length() == 0:
                to_player = Vec(1, 0)
            radial = to_player.normalize()
            # perpendicular vector for tangential/orbit motion
            tangential = Vec(-radial.y, radial.x)
            # decide direction (keep current dir sign to remain consistent)
            sign = 1.0 if self.dir.dot(tangential) >= 0 else -1.0
            tangential = tangential * sign
            # weighting from config
            # use per-UFO randomized weights
            t_w = getattr(self, 'orbit_tangential', float(getattr(C, 'UFO_ORBIT_TANGENTIAL', 0.85)))
            r_w = getattr(self, 'orbit_radial', float(getattr(C, 'UFO_ORBIT_RADIAL', 0.15)))
            desired = (tangential * t_w + radial * r_w)
            if desired.length_squared() == 0:
                desired = tangential
            else:
                desired = desired.normalize()
            # smooth turning towards desired direction
            max_turn = getattr(self, 'orbit_max_turn', float(getattr(C, 'UFO_ORBIT_MAX_TURN', 3.0)))
            # simple lerp of direction based on dt*max_turn
            lerp = min(1.0, dt * max_turn)
            self.dir = (self.dir * (1.0 - lerp) + desired * lerp).normalize()
            self.pos += self.dir * self.speed * dt
        else:
            self.pos += self.dir * self.speed * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos
        # manage shot frame timer
        if self._shot_timer > 0:
            self._shot_timer = max(0.0, self._shot_timer - dt)
            if self._shot_timer == 0.0:
                self._show_shot = False

    def get_mask(self):
        # Prefer pixel-perfect mask from embedded frames when available.
        if OVNI_FRAMES:
            # choose current visual frame (shot if showing, otherwise base)
            key = 'shot' if self._show_shot and 'shot' in OVNI_FRAMES else 'base'
            frames = OVNI_FRAMES.get(key, [])
            if frames:
                frame = frames[0]
                if isinstance(frame, dict) and 'pixels' in frame:
                    # Use full rectangular mask for UFO (ignore transparency)
                    w = int(frame['w'])
                    h = int(frame['h'])
                    base_scale = float(getattr(C, 'UFO_PIXEL_SCALE', 1))
                    float_scale = max(0.1, base_scale)
                    target_w = max(1, int(w * float_scale))
                    target_h = max(1, int(h * float_scale))
                    surf = pg.Surface((target_w, target_h), pg.SRCALPHA)
                    rect_full = pg.Rect(0, 0, target_w, target_h)
                    pg.draw.rect(surf, (255, 255, 255, 255), rect_full)
                    mask = pg.mask.from_surface(surf)
                    rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
                    return (mask, rect)

        # Fallback: approximate mask as an ellipse based on radius
        w, h = int(self.r * 2), int(self.r)
        surf = pg.Surface((w, h), pg.SRCALPHA)
        rect = pg.Rect(0, 0, w, h)
        pg.draw.ellipse(surf, (255, 255, 255), rect)
        mask = pg.mask.from_surface(surf)
        rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        return (mask, rect)

    # Desenha o corpo do UFO como elipse
    def draw(self, surf: pg.Surface):
        # prefer embedded OVNI frames when available
        if OVNI_FRAMES:
            key = 'shot' if self._show_shot and 'shot' in OVNI_FRAMES else 'base'
            frames = OVNI_FRAMES.get(key, [])
            if frames:
                frame = frames[0]
                if isinstance(frame, dict) and 'pixels' in frame:
                    w = int(frame['w'])
                    h = int(frame['h'])
                    pixels = frame['pixels']
                    base_scale = float(getattr(C, 'UFO_PIXEL_SCALE', 1))
                    float_scale = max(0.1, base_scale)
                    # draw original unscaled sprite into surf0 then scale smoothly
                    surf0 = pg.Surface((w, h), pg.SRCALPHA)
                    for y, row in enumerate(pixels):
                        for x, col in enumerate(row):
                            r, g, b, a = col
                            if a == 0:
                                continue
                            surf0.set_at((x, y), (r, g, b, a))
                    target_w = max(1, int(w * float_scale))
                    target_h = max(1, int(h * float_scale))
                    spr = pg.transform.smoothscale(surf0, (target_w, target_h))
                    rect = spr.get_rect(center=(int(self.pos.x), int(self.pos.y)))
                    surf.blit(spr, rect)
                    return

        # fallback: draw simple ellipse if no embedded frames
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
    def get_mask(self):
        # circular mask similar to Bullet
        try:
            r = int(max(1, self.r))
        except Exception:
            r = 2
        w = h = r * 2
        surf = pg.Surface((w, h), pg.SRCALPHA)
        pg.draw.circle(surf, (255, 255, 255), (r, r), r)
        mask = pg.mask.from_surface(surf)
        rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        return (mask, rect)


class Barrel(pg.sprite.Sprite):
    def __init__(self, x: float, target_y: float):
        super().__init__()
        from random import uniform
        self.pos = Vec(x, -10)
        self.target_y = target_y
        self.vel = Vec(0, C.BARREL_FALL_SPEED)
        self.landed = False
        # HP: how many hits it can take before destroyed
        self.hp = int(getattr(C, 'BARREL_HP', 2))
        # radius for collisions; default, may be overridden from frame size
        self.r = int(getattr(C, 'BARREL_RADIUS', 12))
        # choose barrel kind at spawn (e.g. 'base' or 'tnt') so each barrel
        # has its own visual type from the beginning
        if BARREL_FRAMES:
            try:
                from random import choice
                keys = list(BARREL_FRAMES.keys())
                self.kind = choice(keys) if keys else 'base'
            except Exception:
                self.kind = 'base'
        else:
            self.kind = 'base'
        # damaged flag for visual state (does not change the kind)
        self.damaged = False
        # if we have an embedded frame for this kind, derive radius from it
        try:
            if BARREL_FRAMES and self.kind in BARREL_FRAMES and BARREL_FRAMES[self.kind]:
                sample = BARREL_FRAMES[self.kind][0]
                if isinstance(sample, dict) and 'w' in sample and 'h' in sample:
                    scale = int(getattr(C, 'BARREL_PIXEL_SCALE', 1))
                    scale = max(1, scale)
                    w = int(sample['w']) * scale
                    h = int(sample['h']) * scale
                    self.r = max(self.r, max(6, int(min(w, h) * 0.45)))
        except Exception:
            pass
        # rect used by sprite groups
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        if not self.landed:
            self.pos += self.vel * dt
            if self.pos.y >= self.target_y:
                self.pos.y = self.target_y
                self.vel = Vec(0, 0)
                self.landed = True
        # manage explosion timer if triggered (for TNT barrels)
        if getattr(self, 'exploded', False):
            self.explosion_timer = max(0.0, getattr(self, 'explosion_timer', 0.0) - dt)
            if self.explosion_timer <= 0.0:
                # end of visual explosion, remove barrel
                self.kill()
                return
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # If this barrel is exploding (TNT), draw explosion circle and skip normal sprite
        if getattr(self, 'exploded', False) and self.kind == 'tnt':
            radius = int(getattr(self, 'explosion_radius', getattr(C, 'BARREL_TNT_EXPLOSION_RADIUS', 80)))
            color = (255, 140, 0)
            try:
                pg.draw.circle(surf, color, (int(self.pos.x), int(self.pos.y)), radius, width=3)
            except Exception:
                # fallback: use helper draw_circle (white)
                from utils import draw_circle
                draw_circle(surf, self.pos, radius)
            return
        # prefer embedded barrel frames
        if BARREL_FRAMES:
            key = self.kind
            frames = BARREL_FRAMES.get(key, [])
            if frames:
                frame = frames[0]
                if isinstance(frame, dict) and 'pixels' in frame:
                    w = int(frame['w'])
                    h = int(frame['h'])
                    pixels = frame['pixels']
                    scale = int(getattr(C, 'BARREL_PIXEL_SCALE', 2))
                    scale = max(1, scale)
                    spr = pg.Surface((w * scale, h * scale), pg.SRCALPHA)
                    for y, row in enumerate(pixels):
                        for x, col in enumerate(row):
                            r, g, b, a = col
                            if a == 0:
                                continue
                            rect = pg.Rect(x * scale, y * scale, scale, scale)
                            pg.draw.rect(spr, (r, g, b, a), rect)
                    rect = spr.get_rect(center=(int(self.pos.x), int(self.pos.y)))
                    surf.blit(spr, rect)
                    return

        # fallback: draw simple brown rectangle
        w = self.r * 2
        h = self.r * 2
        rect = pg.Rect(0, 0, w, h)
        rect.center = self.pos
        pg.draw.rect(surf, (150, 90, 20), rect)

    def get_mask(self):
        # Use embedded frames for precise mask when available
        if BARREL_FRAMES:
            key = self.kind
            frames = BARREL_FRAMES.get(key, [])
            if frames:
                frame = frames[0]
                if isinstance(frame, dict) and 'pixels' in frame:
                    # Use a full rectangular mask (ignore transparency)
                    w = int(frame['w'])
                    h = int(frame['h'])
                    scale = int(getattr(C, 'BARREL_PIXEL_SCALE', 2))
                    scale = max(1, scale)
                    surf = pg.Surface((w * scale, h * scale), pg.SRCALPHA)
                    # Fill entire surface as solid for simpler collisions
                    rect_full = pg.Rect(0, 0, w * scale, h * scale)
                    pg.draw.rect(surf, (255, 255, 255, 255), rect_full)
                    mask = pg.mask.from_surface(surf)
                    rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
                    return (mask, rect)

        # fallback ellipse
        w, h = int(self.r * 2), int(self.r * 2)
        surf = pg.Surface((w, h), pg.SRCALPHA)
        rect = pg.Rect(0, 0, w, h)
        pg.draw.ellipse(surf, (255, 255, 255), rect)
        mask = pg.mask.from_surface(surf)
        rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        return (mask, rect)

    def hit(self):
        # Called when struck by a bullet
        self.hp -= 1
        if self.hp <= 0:
            # If this is a TNT barrel, trigger an explosion visual instead
            if getattr(self, 'kind', 'base') == 'tnt':
                try:
                    import sounds
                    sounds.play_explosion()
                except Exception:
                    pass
                self.exploded = True
                self.explosion_timer = float(getattr(C, 'BARREL_TNT_EXPLOSION_TIME', 0.28))
                self.explosion_radius = int(getattr(C, 'BARREL_TNT_EXPLOSION_RADIUS', 80))
                # stop movement and mark landed so it doesn't fall further
                self.vel = Vec(0, 0)
                self.landed = True
                return
            try:
                import sounds
                sounds.play_explosion()
            except Exception:
                pass
            self.kill()
        else:
            self.damaged = True