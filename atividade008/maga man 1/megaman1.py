import os
import pygame
from pygame.locals import *
from sys import exit
import traceback

# --- Configuration and Initialization ---
pygame.init()

SCREEN_W = 640
SCREEN_H = 480
COLOR_BLACK = (0, 0, 0)
FPS = 60
GROUND_Y = SCREEN_H - 50

main_screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption('Mega Man X Tribute')
game_clock = pygame.time.Clock()

SCRIPT_DIR = os.path.dirname(__file__)
ASSET_DIR = os.path.join(SCRIPT_DIR, 'mega_man')

# --- Background Loading ---
try:
    bg_path = os.path.join(ASSET_DIR, 'bckg.png')
    background_img = pygame.image.load(bg_path).convert()
    background_img = pygame.transform.scale(background_img, (SCREEN_W, SCREEN_H))
except pygame.error:
    background_img = None


# --- Protagonist Class ---
class Protagonist(pygame.sprite.Sprite):
    """Main character entity. Handles movement, jumping, running, and shooting."""

    def __init__(self):
        super().__init__()

        # Sprite setup and scaling
        self.scale_val = 3.0
        self.frames_walk = [self._load_sprite(i) for i in range(1, 4)]
        self.frames_run = [self._load_sprite(i) for i in range(4, 7)]
        self.jump_image = self._load_sprite(7)
        self.shoot_image = self._load_sprite(8)

        # Animation state
        self.frame_index = 0.0
        self.anim_speed = 0.25
        self.image = self.frames_walk[0]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_W // 2, GROUND_Y - self.rect.height // 2)

        # Movement control
        self.speed_x = 0
        self.speed_y = 0
        self.walk_speed = 4
        self.run_speed = 8
        self.jump_power = -15
        self.gravity = 1
        self.on_ground = True
        self.facing_right = True
        self.is_running = False

        # Shooting control
        self.is_shooting = False
        self.last_shot_time = 0
        self.shot_delay = 250  # milliseconds between shots when holding

        # Run timing - hold for 2000 ms to enable run
        self.hold_start_time = None
        self.hold_threshold = 100  # ms

    def _load_sprite(self, index: int) -> pygame.Surface:
        """Load and scale a sprite image from disk."""
        path = os.path.join(ASSET_DIR, f'sprite_{index}.png')
        sprite = pygame.image.load(path).convert_alpha()
        w, h = sprite.get_size()
        return pygame.transform.smoothscale(
            sprite, (int(w * self.scale_val), int(h * self.scale_val))
        )

    def jump(self):
        """Apply vertical impulse when grounded."""
        if self.on_ground:
            self.speed_y = self.jump_power
            self.on_ground = False

    def update(self):
        """Update physics, movement and select current frame."""
        # Apply gravity and vertical movement
        self.speed_y += self.gravity
        self.rect.y += self.speed_y

        # Ground collision
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.speed_y = 0
            self.on_ground = True

        # Horizontal movement and clamp on-screen
        self.rect.x += self.speed_x
        self.rect.x = max(0, min(self.rect.x, SCREEN_W - self.rect.width))

        # Choose and set sprite frame
        old_center = self.rect.center
        frame = self._select_frame()
        self.image = pygame.transform.flip(frame, not self.facing_right, False)
        self.rect = self.image.get_rect(center=old_center)

    def _select_frame(self) -> pygame.Surface:
        #etermine which frame to render.
        if not self.on_ground:
            return self.jump_image

        if self.is_shooting:
            # Keep shooting sprite displayed while the shoot key is held.
            return self.shoot_image

        if self.speed_x != 0:
            # Advance animation index and return appropriate frame set.
            self.frame_index += self.anim_speed
            frames = self.frames_run if self.is_running else self.frames_walk
            if self.frame_index >= len(frames):
                self.frame_index = 0.0
            return frames[int(self.frame_index)]

        # Idle frame
        self.frame_index = 0.0
        return self.frames_walk[0]


# --- Projectile Class ---
class Projectile(pygame.sprite.Sprite):
    """Projectile fired by protagonist."""

    def __init__(self, x, y, direction):
        super().__init__()

        path = os.path.join(SCRIPT_DIR, 'shot', 'sprite_shot.png')
        shot_img = pygame.image.load(path).convert_alpha()
        shot_img = pygame.transform.smoothscale(
            shot_img,
            (int(shot_img.get_width() * 2.5), int(shot_img.get_height() * 2.5)),
        )
        if direction == -1:
            shot_img = pygame.transform.flip(shot_img, True, False)

        self.image = shot_img
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.speed = 10.0
        # small translucent circular trail surface
        self.trail = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.trail, (100, 200, 255, 150), (4, 4), 4)

    def update(self):
        """Advance projectile and render trail; destroy when off-screen."""
        self.rect.x += self.speed * self.direction
        main_screen.blit(self.trail, (self.rect.centerx - 4, self.rect.centery - 4))
        if self.rect.right < 0 or self.rect.left > SCREEN_W:
            self.kill()


# --- Game Initialization ---
player = Protagonist()
all_sprites = pygame.sprite.Group(player)
shots = pygame.sprite.Group()

# --- Main Game Loop ---
while True:
    # Draw background
    if background_img:
        main_screen.blit(background_img, (0, 0))
    else:
        main_screen.fill(COLOR_BLACK)

    keys = pygame.key.get_pressed()
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        try:
            if event.type == QUIT:
                pygame.quit()
                exit()

            # Key press events
            if event.type == KEYDOWN:
                if event.key in (K_a, K_LEFT):
                    player.facing_right = False
                    player.speed_x = -player.walk_speed
                    # record time when movement key first pressed
                    player.hold_start_time = current_time

                elif event.key in (K_d, K_RIGHT):
                    player.facing_right = True
                    player.speed_x = player.walk_speed
                    player.hold_start_time = current_time

                elif event.key in (K_w, K_UP):
                    # proteger jump() com try/except para capturar erro
                    try:
                        player.jump()
                    except Exception:
                        print('Erro ao executar jump():')
                        traceback.print_exc()

                elif event.key in (K_e, K_SPACE):
                    try:
                        # detectar se o tiro foi iniciado no ar
                        player.shoot_pressed_in_air = not player.on_ground
                        player.is_shooting = True
                        player.last_shot_time = 0
                    except Exception:
                        print('Erro ao iniciar tiro:')
                        traceback.print_exc()

            # Key release events
            if event.type == KEYUP:
                if event.key in (K_a, K_LEFT, K_d, K_RIGHT):
                    player.speed_x = 0
                    player.is_running = False
                    player.hold_start_time = None

                elif event.key in (K_e, K_SPACE):
                    player.is_shooting = False
                    player.last_shot_time = current_time
                    # resetar flag ao soltar a tecla de tiro
                    player.shoot_pressed_in_air = False
        except Exception:
            print('Erro no processamento de evento:')
            traceback.print_exc()

    # Running: check if movement key has been held long enough
    if player.hold_start_time is not None:
        elapsed = current_time - player.hold_start_time
        player.is_running = elapsed >= player.hold_threshold
        if player.is_running:
            # maintain run speed while running state is active
            player.speed_x = player.run_speed if player.facing_right else -player.run_speed

    # Shooting: spawn projectiles repeatedly while shoot key is held,
    # subject to shot_delay interval. This keeps shoot_image visible as long
    # as the key is held and produces repeated shots at shot_delay cadence.
    if player.is_shooting:
        if current_time - player.last_shot_time >= player.shot_delay:
            x_offset = 45 * (1 if player.facing_right else -1)
            y_offset = -2
            shot = Projectile(
                player.rect.centerx + x_offset,
                player.rect.centery + y_offset,
                1 if player.facing_right else -1,
            )
            shots.add(shot)
            all_sprites.add(shot)
            player.last_shot_time = current_time

    # Update and draw sprites
    all_sprites.update()
    all_sprites.draw(main_screen)

    # Flip display and cap FPS
    pygame.display.flip()
    game_clock.tick(FPS)