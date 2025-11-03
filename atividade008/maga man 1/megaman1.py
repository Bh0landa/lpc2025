import os
import pygame
from pygame.locals import *
from sys import exit

pygame.init()

# --- Global Settings (PEP 8 standard: CONSTANTS_UPPER_SNAKE_CASE) ---
SCREEN_W = 640
SCREEN_H = 480
COLOR_BLACK = (0, 0, 0)
FPS = 60

# --- Game Logic Constants ---
GROUND_Y = SCREEN_H - 50

# --- Initialization ---
main_screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption('Mega Man X Tribute')
game_clock = pygame.time.Clock()

# --- Asset Loading ---
script_dir = os.path.dirname(__file__)
assets_directory = os.path.join(script_dir, 'mega_man')

# Load Background Image (Adjusted path)
try:
    background_path = os.path.join(assets_directory, 'bckg.png')
    background_img = pygame.image.load(background_path).convert()
    background_img = pygame.transform.scale(background_img, (SCREEN_W, SCREEN_H))
except pygame.error as e:
    print(f"Error loading background image (bckg.png): {e}")
    background_img = None


class Protagonist(pygame.sprite.Sprite):
    """Represents the player character, Mega Man X."""
    def __init__(self):
        super().__init__()
        
        self.animation_frames: list[pygame.Surface] = []
        scale_val = 3.0
        self.num_run_frames = 8

        # Load sprites (1 to 8) from the 'mega_man' folder
        for i in range(1, self.num_run_frames + 1):
            file_name = f'sprite_{i}.png'
            file_path = os.path.join(assets_directory, file_name)
            sprite_image: pygame.Surface = pygame.image.load(file_path).convert_alpha()
            w, h = sprite_image.get_size()
            new_dim = (int(w * scale_val), int(h * scale_val))
            sprite_image = pygame.transform.smoothscale(sprite_image, new_dim)
            self.animation_frames.append(sprite_image)

        # Initial state setup
        self.frame_index = 0.0
        self.anim_speed = 0.25
        self.image: pygame.Surface = self.animation_frames[int(self.frame_index)]
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.center = (SCREEN_W // 2, GROUND_Y - self.rect.height // 2)

        # Movement variables
        self.speed_x = 0
        self.speed_y = 0
        self.walk_speed = 5
        self.jump_power = -15
        self.gravity = 1
        self.on_ground = True
        self.facing_right = True

        # Shooting variables
        self.is_shooting = False
        self.shot_frame_index = 6
        self.prev_frame_idx = -1
        self.should_fire = False

    def jump(self):
        """Initiates a jump if the character is on the ground."""
        if self.on_ground:
            self.speed_y = self.jump_power
            self.on_ground = False

    def shoot(self):
        """Starts the shooting animation sequence."""
        if not self.is_shooting:
            self.is_shooting = True
            # Reset animation to start the cycle, ensuring shot trigger
            self.frame_index = 0.0 

    def update(self):
        """Updates the character's movement, animation, and state."""
        
        # 1. Apply Gravity and Vertical Movement
        self.speed_y += self.gravity
        self.rect.y += self.speed_y

        # 2. Ground Collision Check
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.speed_y = 0
            self.on_ground = True
            
        # 3. Horizontal Movement
        self.rect.x += self.speed_x

        # 4. Screen Boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_W:
            self.rect.right = SCREEN_W

        # 5. Animation Logic
        
        if self.is_shooting:
            # Continue animation (Run cycle is also the shooting cycle in this setup)
            self.frame_index += self.anim_speed
            if self.frame_index >= self.num_run_frames:
                self.frame_index = 0.0 # Loop the run/shoot cycle
        elif self.speed_x != 0 and self.on_ground:
            # Running animation
            self.frame_index += self.anim_speed
            if self.frame_index >= self.num_run_frames:
                self.frame_index = 0.0
        else:
            # IDLE animation (First frame)
            self.frame_index = 0.0
            self.is_shooting = False

        current_frame_idx = int(self.frame_index)

        # 6. Sprite Update and Flip
        old_center = self.rect.center
        
        # Get the current frame (using modulo to ensure index stays within range)
        raw_image = self.animation_frames[current_frame_idx % self.num_run_frames]
        
        # Apply horizontal flip based on facing direction
        if not self.facing_right:
            self.image = pygame.transform.flip(raw_image, True, False)
        else:
            self.image = raw_image

        self.rect = self.image.get_rect()
        self.rect.center = old_center

        # 7. Shooting Trigger Logic
        # Fire only when transitioning into the shot frame (index 6)
        if (self.is_shooting and 
            current_frame_idx != self.prev_frame_idx and 
            current_frame_idx == self.shot_frame_index):
            
            self.should_fire = True
            self.is_shooting = False # Disable shooting state after trigger
        else:
            self.should_fire = False
            
        self.prev_frame_idx = current_frame_idx


class Projectile(pygame.sprite.Sprite):
    """Represents a shot fired by the Protagonist."""
    # Added 'direction' argument to control shot direction based on character facing
    def __init__(self, start_x: int, start_y: int, velocity: float = 8.0, direction: int = 1):
        super().__init__()
        script_base_dir = os.path.dirname(__file__)
        assets_dir_shot = os.path.join(script_base_dir, 'shot')
        shot_path = os.path.join(assets_dir_shot, 'sprite_shot.png')
        shot_img_raw = pygame.image.load(shot_path).convert_alpha()
        
        scale_val = 3
        new_shot_size = (int(shot_img_raw.get_width() * scale_val), 
                         int(shot_img_raw.get_height() * scale_val))
        self.image = pygame.transform.smoothscale(shot_img_raw, new_shot_size)
        
        # Flip projectile image if shooting left
        if direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)
            
        self.rect = self.image.get_rect()
        self.pos_x = float(start_x)
        self.rect.center = (int(self.pos_x), int(start_y))
        
        self.vel_x = float(velocity * direction)

    def update(self):
        """Updates the projectile's position."""
        self.pos_x += self.vel_x
        self.rect.x = int(self.pos_x)
        
        # Remove shot when it goes off screen
        if self.rect.left > SCREEN_W or self.rect.right < 0:
            self.kill()

# --- Game Setup ---
all_game_objects = pygame.sprite.Group()
main_character = Protagonist()
all_game_objects.add(main_character)
projectile_group = pygame.sprite.Group()

# --- Main Game Loop ---
while True:
    # 1. Draw Background
    if background_img:
        main_screen.blit(background_img, (0, 0))
    else:
        main_screen.fill(COLOR_BLACK)
        
    # 2. Event Handling
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
        
        # Key Press (KEYDOWN) logic
        if event.type == KEYDOWN:
            if event.key == K_a or event.key == K_LEFT:
                main_character.speed_x = -main_character.walk_speed
                main_character.facing_right = False
            elif event.key == K_d or event.key == K_RIGHT:
                main_character.speed_x = main_character.walk_speed
                main_character.facing_right = True
            elif event.key == K_w or event.key == K_UP:
                main_character.jump()
            elif event.key == K_e:
                main_character.shoot()

        # Key Release (KEYUP) logic
        if event.type == KEYUP:
            if (event.key == K_a or event.key == K_LEFT or 
                    event.key == K_d or event.key == K_RIGHT):
                main_character.speed_x = 0
            
    # 3. Update Sprites
    all_game_objects.update()
    
    # 4. Shooting Logic
    if getattr(main_character, 'should_fire', False):
        x_offset = 40
        y_offset = -2
        
        # Determine shot direction and adjust spawn point
        shot_direction = 1 if main_character.facing_right else -1
        spawn_x = main_character.rect.centerx + (x_offset * shot_direction)
        
        shot_instance = Projectile(spawn_x, 
                                   main_character.rect.centery + y_offset, 
                                   direction=shot_direction)
        projectile_group.add(shot_instance)

    # 5. Draw Objects
    projectile_group.update()
    projectile_group.draw(main_screen)
    all_game_objects.draw(main_screen)
    
    # 6. Update Display and Cap FPS
    pygame.display.flip()
    game_clock.tick(FPS)