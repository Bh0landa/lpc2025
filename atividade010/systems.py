# Module `systems.py` — short description of this module.
import math
from random import uniform

import pygame as pg

import config as C
from sprites import Asteroid, Ship, UFO, Barrel
from utils import Vec, rand_edge_pos, rand_unit_vec
from sprites import UFObullet
import sounds
from utils import get_logger

logger = get_logger("systems")


# Class `World` — describe responsibility and main methods.
# Game world that manages entities, score and global game logic.
# Game world that manages entities, scoring and global game logic.
class World:
    # Function `__init__(self)` — describe purpose and behavior.
    # Initialize the world state: player, sprite groups, timers and difficulty state.

    def __init__(self):
        # Create the player's ship, sprite groups and game variables
        self.ship = Ship(Vec(C.WIDTH / 2, C.HEIGHT / 2))
        self.bullets = pg.sprite.Group()
        self.ufo_bullets = pg.sprite.Group()
        self.asteroids = pg.sprite.Group()
        self.ufos = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group(self.ship)
        self.score = 0
        self.lives = C.START_LIVES
        # continuous spawn: timers to control asteroid spawning
        self.asteroid_spawn_timer = 0.0
        self.asteroid_spawn_interval = float(
            getattr(C, "AST_SPAWN_INTERVAL_BASE", 1.5)
        )
        self.safe = C.SAFE_SPAWN_TIME
        self.ufo_timer = C.UFO_SPAWN_EVERY
        self.last_barrel_spawn = 0.0
        self.next_barrel_spawn = uniform(
            C.BARREL_SPAWN_INTERVAL_MIN, C.BARREL_SPAWN_INTERVAL_MAX
        )
        self.barrels = pg.sprite.Group()

    # (Wave system removed) asteroids now spawn continuously; difficulty scales with score

    def spawn_asteroid(self, pos: Vec, vel: Vec, size: str):
        # Create and add an asteroid to the world at `pos` with velocity `vel`.
        # This function centralizes asteroid creation so additional logic
        # (scoring, effects) can be applied in one place.
        a = Asteroid(pos, vel, size)
        self.asteroids.add(a)
        self.all_sprites.add(a)

    # Function `spawn_ufo(self)` — describe purpose and behavior.

    def spawn_ufo(self):
        # Spawn a UFO (small or large) at a random screen edge.
        # Small UFOs are biased to aim toward the player; large ones travel straight.
        small = uniform(0, 1) < 0.5
        y = uniform(0, C.HEIGHT)
        x = 0 if uniform(0, 1) < 0.5 else C.WIDTH
        ufo = UFO(Vec(x, y), small)
        # Adjust initial direction so small UFOs aim toward the player
        if small:
            to_player = self.ship.pos - ufo.pos
            if to_player.length() > 0:
                to_player = to_player.normalize()
            ufo.dir = (
                ufo.dir * (1 - ufo.aim) + to_player * ufo.aim
            ).normalize()
        else:
            ufo.dir = Vec(1, 0) if x == 0 else Vec(-1, 0)

        sounds.play_ufo_spawn()
        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

    # Function `try_fire(self)` — describe purpose and behavior.

    def try_fire(self):
        # Attempt to fire a bullet from the player's ship.
        # The ship's internal cooldown (`Ship.fire`) controls rate of fire.
        b = self.ship.fire()
        if b:
            self.bullets.add(b)
            self.all_sprites.add(b)
            try:
                sounds.play_shot()
            except Exception as e:
                logger.warning(f"Failed to play shot sound: {e}")

    # Function `hyperspace(self)` — describe purpose and behavior.

    def hyperspace(self):
        # Teleport the player's ship to a random position and apply score penalty.
        # This is a risky but useful defensive mechanic.
        self.ship.hyperspace()
        self.score = max(0, self.score - C.HYPERSPACE_COST)

    # Function `update(self, dt, keys)` — describe purpose and behavior.

    def update(self, dt: float, keys):
        # Update all sprites and main timers.
        # Note: UFO.update accepts (dt, ship_pos) so we pass the player's position;
        # other sprites implement update(dt) only.
        for spr in list(self.all_sprites):
            if isinstance(spr, UFO):
                spr.update(dt, self.ship.pos)
            else:
                spr.update(dt)
        self.ufo_bullets.update(dt)
        self.ship.control(keys, dt)
        # The ship is updated via `all_sprites.update`

        # Spawn and safety timers
        if self.safe > 0:
            self.safe -= dt
            self.ship.invuln = 0.5
        self.ufo_timer -= dt
        if self.ufo_timer <= 0:
            # difficulty scales with score (higher score -> more frequent spawns)
            difficulty = 1.0 + (float(self.score) / C.AST_DIFFICULTY_SCORE_SCALE)
            
            configured_count = getattr(C, "UFO_SPAWN_COUNT", 1)
            
            # determine desired concurrent UFOs (scale slowly with difficulty)
            desired_concurrent = min(configured_count, 1 + int(difficulty / 2))
            # spawn only up to the difference between desired and current active UFOs
            spawn_count = max(0, desired_concurrent - len(self.ufos))
            for _ in range(spawn_count):
                # Spawn up to `spawn_count` UFOs to reach desired concurrency.
                self.spawn_ufo()
            # shorten interval as difficulty rises
            self.ufo_timer = float(getattr(C, "UFO_SPAWN_EVERY", 20.0)) / max(0.001, difficulty)

        # barrel spawn (intervals scale with difficulty)
        # Barrel spawn management: spawn barrels periodically (interval may scale with difficulty)
        self.last_barrel_spawn += dt
        if self.last_barrel_spawn >= self.next_barrel_spawn:
            self.last_barrel_spawn = 0.0
            difficulty = 1.0 + (float(self.score) / C.AST_DIFFICULTY_SCORE_SCALE)
            self.next_barrel_spawn = uniform(
                C.BARREL_SPAWN_INTERVAL_MIN, C.BARREL_SPAWN_INTERVAL_MAX
            ) / max(0.001, difficulty)
            # Create a barrel that falls from above to `target_y`.
            x = uniform(20, C.WIDTH - 20)
            target_y = uniform(C.HEIGHT * 0.5, C.HEIGHT - 40)
            barrel = Barrel(x, target_y)
            self.all_sprites.add(barrel)
            self.barrels.add(barrel)

        # UFO firing logic
        for ufo in list(self.ufos):
            if hasattr(ufo, "fire_cool"):
                ufo.fire_cool = max(0.0, ufo.fire_cool - dt)
                if ufo.fire_cool <= 0:
                    dir_to_player = self.ship.pos - ufo.pos
                    if dir_to_player.length() == 0:
                        dir_to_player = rand_unit_vec()
                    else:
                        dir_to_player = dir_to_player.normalize()
                    aim = ufo.aim if hasattr(ufo, "aim") else 0.3
                    fire_dir = (
                        ufo.dir * (1 - aim) + dir_to_player * aim
                    ).normalize()
                    # Use a scaled bullet speed for UFO shots (slightly slower than player)
                    vel = fire_dir * (C.BULLET_SPEED * 0.8)
                    b = UFObullet(ufo.pos + fire_dir * (ufo.r + 6), vel)
                    self.ufo_bullets.add(b)
                    self.all_sprites.add(b)
                    # mark ufo to display 'shot' frame briefly (if it supports embedded frames)
                    # mark ufo to display 'shot' frame briefly (if it supports embedded frames)
                    ufo._show_shot = True
                    ufo._shot_timer = C.UFO_SHOT_TIMER
                    
                    # reset the UFO fire cooldown
                    ufo.fire_cool = ufo.fire_rate
                    try:
                        sounds.play_ufo_shot()
                    except Exception as e:
                        logger.warning(f"Failed to play UFO shot sound: {e}")

        # Resolve collisions after updates (bullets, asteroids, UFOs, barrels)
        self.handle_collisions()

        # Continuous asteroid spawning (difficulty scales with score)
        # `difficulty` already computed above from score
        difficulty = 1.0 + (float(self.score) / C.AST_DIFFICULTY_SCORE_SCALE)
        self.asteroid_spawn_timer -= dt
        if self.asteroid_spawn_timer <= 0:
            # compute next interval (shortens as difficulty increases)
            interval = max(
                float(getattr(C, "AST_SPAWN_INTERVAL_MIN", 0.4)),
                float(getattr(C, "AST_SPAWN_INTERVAL_BASE", 1.5))
                / max(0.001, difficulty),
            )
            self.asteroid_spawn_timer = interval
            # determine how many to spawn this tick (increase slowly with score)
            spawn_count = 1 + int(self.score / C.AST_SCORE_SPAWN_FACTOR)
            spawn_count = min(spawn_count, C.AST_MAX_SPAWN_COUNT)
            for _ in range(spawn_count):
                # Spawn asteroid at a random screen edge, avoiding the player
                pos = rand_edge_pos()
                # avoid spawns too close to the player
                tries = 0
                while (pos - self.ship.pos).length() < C.AST_SPAWN_MIN_DIST and tries < C.AST_SPAWN_MAX_TRIES:
                    pos = rand_edge_pos()
                    tries += 1
                ang = uniform(0, math.tau)
                base_speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX)
                # scale speed modestly with difficulty
                speed = base_speed * (1.0 + (difficulty - 1.0) * C.AST_SPEED_SCALE)
                vel = Vec(math.cos(ang), math.sin(ang)) * speed
                # select size probabilistically: more small/medium at higher difficulty
                prob_m = min(0.4, (difficulty - 1.0) * 0.15)
                prob_s = min(0.2, (difficulty - 1.0) * 0.05)
                r = uniform(0, 1)
                if r < prob_s:
                    size = "S"
                elif r < (prob_s + prob_m):
                    size = "M"
                else:
                    size = "L"
                self.spawn_asteroid(pos, vel, size)

    # Function `handle_collisions(self)` — describe purpose and behavior.

    def handle_collisions(self):
        # Collision: player bullets vs asteroids
        hits = pg.sprite.groupcollide(
            self.asteroids,
            self.bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, _ in hits.items():
            self.split_asteroid(ast)

        # Collision: player ship vs objects when not invulnerable
        if self.ship.invuln <= 0 and self.safe <= 0:
            # try pixel-perfect collision using masks when available
            ship_mask, ship_rect = self.ship.get_mask()
            if ship_mask is not None:
                for ast in list(self.asteroids):
                    ast_mask, ast_rect = ast.get_mask()
                    if ast_mask is None:
                        continue
                    offset = (
                        int(ast_rect.left - ship_rect.left),
                        int(ast_rect.top - ship_rect.top),
                    )
                    if ship_mask.overlap(ast_mask, offset):
                        self.ship_die()
                        break
                else:
                    for ufo in list(self.ufos):
                        ufo_mask, ufo_rect = ufo.get_mask()
                        if ufo_mask is None:
                            continue
                        offset = (
                            int(ufo_rect.left - ship_rect.left),
                            int(ufo_rect.top - ship_rect.top),
                        )
                        if ship_mask.overlap(ufo_mask, offset):
                            self.ship_die()
                            break
                    # check barrels with pixel masks
                    for barrel in list(self.barrels):
                        bar_mask, bar_rect = barrel.get_mask()
                        if bar_mask is None:
                            continue
                        offset = (
                            int(bar_rect.left - ship_rect.left),
                            int(bar_rect.top - ship_rect.top),
                        )
                        if ship_mask.overlap(bar_mask, offset):
                            # block traversal: revert ship to previous position if available
                            # block traversal: revert ship to previous position if available
                            if hasattr(self.ship, "_prev_pos") and self.ship._prev_pos is not None:
                                self.ship.pos = Vec(self.ship._prev_pos)
                            else:
                                # fallback: push outside slightly
                                dirv = self.ship.pos - barrel.pos
                                if dirv.length() == 0:
                                    from utils import rand_unit_vec

                                    dirv = rand_unit_vec()
                                dirv_norm = dirv.normalize()
                                desired_dist = (barrel.r + self.ship.r) + 1
                                self.ship.pos = (
                                    barrel.pos + dirv_norm * desired_dist
                                )
                            self.ship.vel = Vec(0, 0)
                            break
            else:
                # fallback to distance checks if masks are not available
                for ast in self.asteroids:
                    if (ast.pos - self.ship.pos).length() < (
                        ast.r + self.ship.r
                    ):
                        self.ship_die()
                        break
                for ufo in self.ufos:
                    if (ufo.pos - self.ship.pos).length() < (
                        ufo.r + self.ship.r
                    ):
                        self.ship_die()
                        break
                # fallback: barrels by radius (non-lethal response)
                for barrel in self.barrels:
                    if (barrel.pos - self.ship.pos).length() < (
                        barrel.r + self.ship.r
                    ):
                        if hasattr(self.ship, "_prev_pos") and self.ship._prev_pos is not None:
                            self.ship.pos = Vec(self.ship._prev_pos)
                        else:
                            dirv = self.ship.pos - barrel.pos
                            if dirv.length() == 0:
                                from utils import rand_unit_vec

                                dirv = rand_unit_vec()
                            dirv_norm = dirv.normalize()
                            desired_dist = (barrel.r + self.ship.r) + 1
                            self.ship.pos = (
                                barrel.pos + dirv_norm * desired_dist
                            )
                        self.ship.vel = Vec(0, 0)
                        break

        # Destroy UFOs that collide with asteroids
        for ufo in list(self.ufos):
            for ast in list(self.asteroids):
                if (ast.pos - ufo.pos).length() < (ast.r + ufo.r):
                    try:
                        sounds.play_explosion()
                    except Exception as e:
                        logger.warning(f"Failed to play explosion sound: {e}")
                    ufo.kill()
                    break

        # Collision: player bullets vs UFOs
        for ufo in list(self.ufos):
            for b in list(self.bullets):
                if (ufo.pos - b.pos).length() < (ufo.r + b.r):
                    score = (
                        C.UFO_SMALL["score"]
                        if ufo.small
                        else C.UFO_BIG["score"]
                    )
                    self.score += score
                    ufo.kill()
                    b.kill()

        # Check if enemy shots hit the player's ship
        for b in list(self.ufo_bullets):
            if (b.pos - self.ship.pos).length() < (
                b.r + self.ship.r
            ) and self.ship.invuln <= 0:
                b.kill()
                self.ship_die()

        # Collision: player bullets vs barrels
        for b in list(self.bullets):
            for barrel in list(self.barrels):
                # attempt to get masks; bullets may not provide masks
                get_b_mask = getattr(b, "get_mask", None)
                if callable(get_b_mask):
                    m_b = get_b_mask()
                else:
                    m_b = (None, None)
                m_bar = barrel.get_mask()
                collided = False
                if (
                    m_b
                    and m_b[0] is not None
                    and m_bar
                    and m_bar[0] is not None
                ):
                    mask_b, rect_b = m_b
                    mask_bar, rect_bar = m_bar
                    offset = (
                        rect_b.left - rect_bar.left,
                        rect_b.top - rect_bar.top,
                    )
                    if mask_bar.overlap(mask_b, offset):
                        collided = True
                else:
                    # fallback radius check — also test segment from previous to current
                    try:
                        prev = getattr(b, "_prev_pos", None)
                        cur = b.pos
                        if prev is None:
                            dist = (cur - barrel.pos).length()
                            if dist <= (b.r + barrel.r):
                                collided = True
                        else:
                            # distance from point to segment
                            pa = barrel.pos
                            p1 = prev
                            p2 = cur
                            seg = p2 - p1
                            seg_len2 = seg.length_squared()
                            if seg_len2 == 0:
                                d = (pa - p1).length()
                            else:
                                t = max(
                                    0.0,
                                    min(1.0, (pa - p1).dot(seg) / seg_len2),
                                )
                                proj = p1 + seg * t
                                d = (pa - proj).length()
                            if d <= (b.r + barrel.r):
                                collided = True
                    except Exception:
                        if (b.pos - barrel.pos).length() <= (b.r + barrel.r):
                            collided = True
                if collided:
                    b.kill()
                    barrel.hit()
                    break

        # Handle TNT barrel explosion area damage (apply once per explosion)
        for barrel in list(self.barrels):
            if getattr(barrel, "exploded", False) and not getattr(
                barrel, "_explosion_applied", False
            ):
                try:
                    radius = float(
                        getattr(
                            barrel,
                            "explosion_radius",
                            getattr(C, "BARREL_TNT_EXPLOSION_RADIUS", 80),
                        )
                    )
                except Exception:
                    radius = getattr(C, "BARREL_TNT_EXPLOSION_RADIUS", 80)
                # Affect asteroids: call split_asteroid to simulate destruction
                for ast in list(self.asteroids):
                    if (ast.pos - barrel.pos).length() <= (radius + ast.r):
                        try:
                            self.split_asteroid(ast)
                        except Exception:
                            try:
                                ast.kill()
                            except Exception:
                                pass
                # Affect UFOs: kill and award score
                for ufo in list(self.ufos):
                    if (ufo.pos - barrel.pos).length() <= (radius + ufo.r):
                        try:
                            score = (
                                C.UFO_SMALL["score"]
                                if ufo.small
                                else C.UFO_BIG["score"]
                            )
                            self.score += score
                        except Exception:
                            pass
                        try:
                            ufo.kill()
                        except Exception:
                            pass
                # Affect ship: apply damage (like a bullet) if within radius
                try:
                    if (self.ship.pos - barrel.pos).length() <= (
                        radius + self.ship.r
                    ) and self.ship.invuln <= 0:
                        self.ship_die()
                except Exception:
                    pass
                # Affect other barrels (chain reaction)
                for other in list(self.barrels):
                    if other is barrel:
                        continue
                    if (other.pos - barrel.pos).length() <= (radius + other.r):
                        other.hit()
                # mark applied so it doesn't reapply each frame
                barrel._explosion_applied = True

    # Function `split_asteroid(self, ast)` — describe purpose and behavior.

    def split_asteroid(self, ast: Asteroid):
        # Fragment asteroid and award points
        self.score += C.AST_SIZES[ast.size]["score"]
        split = C.AST_SIZES[ast.size]["split"]
        pos = Vec(ast.pos)
        ast.kill()
        for s in split:
            dirv = rand_unit_vec()
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * 1.2
            self.spawn_asteroid(pos, dirv * speed, s)

    # Function `ship_die(self)` — describe purpose and behavior.

    def ship_die(self):
        # Handle player ship death
        self.lives -= 1
        self.ship.pos.xy = (C.WIDTH / 2, C.HEIGHT / 2)
        self.ship.vel.xy = (0, 0)
        self.ship.angle = -90
        self.ship.invuln = C.SAFE_SPAWN_TIME
        self.safe = C.SAFE_SPAWN_TIME
        if self.lives < 0:
            # Reset the world when the player loses all lives
            self.__init__()

    # Function `draw(self, surf, font)` — describe purpose and behavior.

    def draw(self, surf: pg.Surface, font: pg.font.Font):
        # Draw all sprites and HUD
        for spr in self.all_sprites:
            spr.draw(surf)

        pg.draw.line(surf, (60, 60, 60), (0, 50), (C.WIDTH, 50), width=1)
        try:
            difficulty = 1.0 + (
                float(self.score)
                / float(getattr(C, "AST_DIFFICULTY_SCORE_SCALE", 1000.0))
            )
            txt = f"SCORE {self.score:06d}   LIVES {self.lives}   DIFF {difficulty:.2f}"
        except Exception:
            txt = f"SCORE {self.score:06d}   LIVES {self.lives}"
        label = font.render(txt, True, C.WHITE)
        surf.blit(label, (10, 10))
