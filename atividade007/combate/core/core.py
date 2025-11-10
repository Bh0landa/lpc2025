import sys
import math
import pygame

# Constants
WIDTH, HEIGHT = 1024, 768
FPS = 60
BACKGROUND_COLOR = (30, 30, 30)
TRIANGLE_COLOR = (255, 0, 0)
TRIANGLE2_COLOR = (0, 0, 255)
TRIANGLE_SIZE = 30
ROTATION_SPEED = 3
MOVEMENT_SPEED = 5
BRAKE = 1
BULLET_SPEED = 8
BULLET_LIFE = 120  # frames

# Firing cooldown (frames) to avoid extremely fast fire rate
FIRE_COOLDOWN = 20  # frames between shots

# Hit/stun/invincibility configuration (frames)
STUN_FRAMES = FPS  # how long the triangle is stunned (cannot move) after being hit
INVINCIBLE_FRAMES = FPS * 3  # seconds of invincibility after stun
BLINK_INTERVAL = 8  # frames between visible/invisible toggles while blinking

def rotate_point(point, angle_degrees):
    angle_radians = math.radians(angle_degrees)
    x, y = point
    cos_theta = math.cos(angle_radians)
    sin_theta = math.sin(angle_radians)
    return (
        x * cos_theta - y * sin_theta,
        x * sin_theta + y * cos_theta,
    )

class Triangle:
    def __init__(self, position):
        self.position = [float(position[0]), float(position[1])]
        self.angle = 0.0
        self.moving = False
        self.moving_back = False
        self.bullets = []
        self._cooldown = 0  # frames until next allowed shot
        self.local_points = [
            (0.0, -TRIANGLE_SIZE),
            (-TRIANGLE_SIZE / 2.0, TRIANGLE_SIZE / 2.0),
            (TRIANGLE_SIZE / 2.0, TRIANGLE_SIZE / 2.0),
        ]

    def get_transformed_points(self):
        transformed = []
        for point in self.local_points:
            rotated = rotate_point(point, self.angle)
            screen_point = (
                rotated[0] + self.position[0], 
                rotated[1] + self.position[1],
            )
            transformed.append(screen_point)
        return transformed

    def get_polygon(self):
        # return triangle points in screen coordinates
        return self.get_transformed_points()

    def collides_with_rect(self, rect):
        # SAT collision test triangle vs axis-aligned rect.
        # Returns (collision, mtv_x, mtv_y) where MTV separates the shapes.
        # Build polygon points for rect (4 points)
        rx, ry, rw, rh = rect.x, rect.y, rect.w, rect.h
        rect_pts = [(rx, ry), (rx+rw, ry), (rx+rw, ry+rh), (rx, ry+rh)]

        poly = self.get_polygon()

        # helper: get normals (axes) from edges for SAT
        def edges_axes(points):
            axes = []
            n = len(points)
            for i in range(n):
                x1, y1 = points[i]
                x2, y2 = points[(i+1)%n]
                # edge vector
                ex, ey = x2 - x1, y2 - y1
                # normal (perp)
                nx, ny = -ey, ex
                # normalize
                length = math.hypot(nx, ny)
                if length == 0:
                    continue
                axes.append((nx/length, ny/length))
            return axes

        axes = edges_axes(poly) + edges_axes(rect_pts)

        # projection helper
        def proj_on_axis(points, axis):
            ax, ay = axis
            vals = [p[0]*ax + p[1]*ay for p in points]
            return min(vals), max(vals)

        mtv_overlap = float('inf')
        mtv_axis = (0.0, 0.0)

        for axis in axes:
            a_min, a_max = proj_on_axis(poly, axis)
            b_min, b_max = proj_on_axis(rect_pts, axis)
            # compute overlap
            overlap = min(a_max, b_max) - max(a_min, b_min)
            if overlap <= 0:
                return (False, 0.0, 0.0)
            # keep smallest overlap for MTV
            if overlap < mtv_overlap:
                mtv_overlap = overlap
                mtv_axis = axis

        # Ensure MTV points from polygon outwards (away from polygon centroid)
        poly_cent_x = sum(p[0] for p in poly) / len(poly)
        poly_cent_y = sum(p[1] for p in poly) / len(poly)
        # direction from polygon centroid along axis
        dot = poly_cent_x * mtv_axis[0] + poly_cent_y * mtv_axis[1]
        # if dot is positive, axis points away from origin in same general dir as centroid
        # we need to ensure MTV moves polygon out of intersection (direction from overlap)
        mtv_x = mtv_axis[0] * mtv_overlap
        mtv_y = mtv_axis[1] * mtv_overlap
        # if translating by mtv moves centroid further into rect, flip
        new_cx = poly_cent_x + mtv_x
        new_cy = poly_cent_y + mtv_y
        # check distance from new centroid to rect center vs old: if new is closer, flip
        rect_cx = rx + rw/2.0
        rect_cy = ry + rh/2.0
        old_dist = (poly_cent_x - rect_cx)**2 + (poly_cent_y - rect_cy)**2
        new_dist = (new_cx - rect_cx)**2 + (new_cy - rect_cy)**2
        if new_dist < old_dist:
            mtv_x = -mtv_x
            mtv_y = -mtv_y
        return (True, mtv_x, mtv_y)

    def rotate(self, direction):
        # Adjust the triangle angle left or right.
        if self.stunned > 0:
            return
        if direction == "left":
            self.angle = (self.angle - ROTATION_SPEED) % 360.0
        elif direction == "right":
            self.angle = (self.angle + ROTATION_SPEED) % 360.0

    def move(self, direction=None):
        # Move the triangle forward relative to its angle.
        # cannot move while stunned
        if getattr(self, 'stunned', 0) > 0:
            # if caller passed 'stop' we still honor it to clear flags
            if direction == 'stop':
                self.moving = False
                self.moving_back = False
            return
        angle_radians = math.radians(self.angle)
        dx = math.sin(angle_radians) * MOVEMENT_SPEED
        dy = -math.cos(angle_radians) * MOVEMENT_SPEED
        if BRAKE == 0:
            # Continuous movement mode
            if direction == "forward":
                self.moving = True
            elif direction == "backward":
                self.moving_back = True
            elif direction == "stop":
                # stop all movement
                self.moving = False
                self.moving_back = False

            if self.moving:
                self.position[0] += dx
                self.position[1] += dy
            if self.moving_back:
                self.position[0] -= dx
                self.position[1] -= dy
        else:
            # Momentary movement mode
            if direction == "forward":
                self.position[0] += dx
                self.position[1] += dy
            elif direction == "backward":
                self.position[0] -= dx
                self.position[1] -= dy

    def shoot(self):
        # spawn a bullet from the triangle nose (first transformed point)
        # enforce cooldown
        if self._cooldown > 0:
            return
        # cannot shoot while stunned
        if getattr(self, 'stunned', 0) > 0:
            return

        pts = self.get_transformed_points()
        if not pts:
            return
        nx, ny = pts[0]
        # compute velocity based on current angle
        rad = math.radians(self.angle)
        vx = math.sin(rad) * BULLET_SPEED
        vy = -math.cos(rad) * BULLET_SPEED
        self.bullets.append({'x': nx, 'y': ny, 'vx': vx, 'vy': vy, 'life': BULLET_LIFE})
        self._cooldown = FIRE_COOLDOWN

    def update(self):
        # per-frame: handle stun, invincibility and visibility blinking
        # initialize attributes if missing (backwards compatible)
        if not hasattr(self, 'stunned'):
            self.stunned = 0
        if not hasattr(self, 'invincible'):
            self.invincible = 0
        if not hasattr(self, 'visible'):
            self.visible = True

        # handle stunned
        if self.stunned > 0:
            self.stunned -= 1
            # ensure not moving while stunned
            self.moving = False
            self.moving_back = False
            # blink while stunned
            self.visible = (self.stunned // BLINK_INTERVAL) % 2 == 0
            # when stun ends, start invincibility
            if self.stunned == 0:
                self.invincible = INVINCIBLE_FRAMES
        elif self.invincible > 0:
            # invincible countdown and blinking
            self.invincible -= 1
            self.visible = (self.invincible // BLINK_INTERVAL) % 2 == 0
        else:
            self.visible = True

    @property
    def is_invincible(self):
        return getattr(self, 'invincible', 0) > 0


class GameState:
    def __init__(self):
        # two players
        self.triangle1 = Triangle(position=(WIDTH // 3, HEIGHT // 2))
        self.triangle2 = Triangle(position=(2 * WIDTH // 3, HEIGHT // 2))

        self.score1 = 0
        self.score2 = 0

        # font for score rendering (expect pygame.init() called by caller)
        self.font = pygame.font.Font(None, 36)

    def handle_input(self, keys):
        # triangle1 (red) uses WASD; triangle2 (blue) uses arrow keys
        if keys[pygame.K_a]:
            self.triangle1.rotate('left')
        if keys[pygame.K_d]:
            self.triangle1.rotate('right')
        # NOTE: backward movement (S) is intentionally not handled here so that
        # the tank-specific module can decide how to map and apply reverse motion.
        if keys[pygame.K_w]:
            self.triangle1.move('forward')
        if keys[pygame.K_SPACE]:
            self.triangle1.shoot()

        if keys[pygame.K_LEFT]:
            self.triangle2.rotate('left')
        if keys[pygame.K_RIGHT]:
            self.triangle2.rotate('right')
        # NOTE: downward/backward movement (DOWN) is intentionally not handled
        # here so that tank.py can implement a local mapping and behavior.
        if keys[pygame.K_UP]:
            self.triangle2.move('forward')
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            self.triangle2.shoot()

        # clear moving_back flags if keys released is handled by caller using move('stop') if needed

    def _tri_centroid(self, tri):
        pts = tri.get_transformed_points()
        if not pts:
            return (tri.position[0], tri.position[1])
        x = sum(p[0] for p in pts) / len(pts)
        y = sum(p[1] for p in pts) / len(pts)
        return (x, y)

    def step(self):
        # update bullets and cooldowns
        for t in (self.triangle1, self.triangle2):
            for b in list(t.bullets):
                b['x'] += b['vx']
                b['y'] += b['vy']
                b['life'] -= 1
                if b['life'] <= 0:
                    try:
                        t.bullets.remove(b)
                    except ValueError:
                        pass
            if t._cooldown > 0:
                t._cooldown -= 1

        # update triangles (stun/invincibility timers)
        for tri in (self.triangle1, self.triangle2):
            tri.update()

        # detect hits: bullets from triangle1 -> triangle2 and vice-versa
        c1 = self._tri_centroid(self.triangle1)
        c2 = self._tri_centroid(self.triangle2)
        COLLIDE_R = TRIANGLE_SIZE * 0.8

        for b in list(self.triangle1.bullets):
            dx = b['x'] - c2[0]
            dy = b['y'] - c2[1]
            if dx * dx + dy * dy <= COLLIDE_R * COLLIDE_R:
                # hit: give point to shooter
                self.score1 += 1
                # apply stun+invincibility to target (triangle2)
                self.triangle2.stunned = STUN_FRAMES
                self.triangle2.invincible = INVINCIBLE_FRAMES
                try:
                    self.triangle1.bullets.remove(b)
                except ValueError:
                    pass

        for b in list(self.triangle2.bullets):
            dx = b['x'] - c1[0]
            dy = b['y'] - c1[1]
            if dx * dx + dy * dy <= COLLIDE_R * COLLIDE_R:
                self.score2 += 1
                # apply stun+invincibility to target (triangle1)
                self.triangle1.stunned = STUN_FRAMES
                self.triangle1.invincible = INVINCIBLE_FRAMES
                try:
                    self.triangle2.bullets.remove(b)
                except ValueError:
                    pass

    def draw(self, surface):
        # bullets
        for t in (self.triangle1, self.triangle2):
            for b in t.bullets:
                pygame.draw.circle(surface, (255,255,255), (int(b['x']), int(b['y'])), 3)

        # scores
        score_surf1 = self.font.render(f"Player 1: {self.score1}", True, TRIANGLE_COLOR)
        score_surf2 = self.font.render(f"Player 2: {self.score2}", True, TRIANGLE2_COLOR)
        surface.blit(score_surf1, (10, 10))
        surface.blit(score_surf2, (WIDTH - score_surf2.get_width() - 10, 10))

        # triangles (respect blinking/visibility when stunned/invincible)
        if getattr(self.triangle1, 'visible', True):
            pygame.draw.polygon(surface, TRIANGLE_COLOR, self.triangle1.get_transformed_points())
        if getattr(self.triangle2, 'visible', True):
            pygame.draw.polygon(surface, TRIANGLE2_COLOR, self.triangle2.get_transformed_points())

def main():
    # Run a GameState-driven demo so controls match tank.py
    global BRAKE
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rotating and Moving Triangle (core demo)")
    clock = pygame.time.Clock()

    state = GameState()

    running = True
    while running:
        clock.tick(FPS)
        screen.fill(BACKGROUND_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        state.handle_input(keys)
        state.step()
        state.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()