import os
import pygame
from pygame.locals import *
from sys import exit

pygame.init()

# Window settings
SCREEN_W = 640
SCREEN_H = 480
# Color definitions
COLOR_BLACK = (0, 0, 0)
FPS = 60 # Frames per second

# Main display surface
main_screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption('Mega Man X Tribute')
game_clock = pygame.time.Clock()

class Protagonist(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        current_script_dir = os.path.dirname(__file__)
        assets_directory = os.path.join(current_script_dir, 'mega_man')

        self.animation_frames: list[pygame.Surface] = []
        scale_val = 3.0

        for i in range(1, 9):
            file_name = f'sprite_{i}.png'
            file_path = os.path.join(assets_directory, file_name)
            sprite_image: pygame.Surface = pygame.image.load(file_path).convert_alpha()
            w, h = sprite_image.get_size()
            new_dim = (int(w * scale_val), int(h * scale_val))
            sprite_image = pygame.transform.smoothscale(sprite_image, new_dim)
            self.animation_frames.append(sprite_image)

        # animation state
        self.frame_index = 0.0
        self.anim_speed = 0.2 # Animation speed multiplier
        self.image: pygame.Surface = self.animation_frames[int(self.frame_index)]
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.center = (SCREEN_W // 2, SCREEN_H // 2)

        # used to detect transition into the shot frame
        self.prev_frame_idx = -1
        self.should_fire = False

    def update(self):
        # advance animation (float index) based on FPS
        # A higher anim_speed means faster animation. 
        # Using game_clock.get_time() for frame-rate independence is often better, 
        # but for simplicity and fixed FPS, a small constant increment works.
        self.frame_index += self.anim_speed 
        if self.frame_index >= len(self.animation_frames):
            self.frame_index = 0.0
            
        current_frame_idx = int(self.frame_index)
        
        # Only update image if the integer frame index changes to avoid unnecessary object re-creation
        if current_frame_idx != self.prev_frame_idx:
            old_center = self.rect.center
            self.image = self.animation_frames[current_frame_idx]
            self.rect = self.image.get_rect()
            self.rect.center = old_center
            
            # trigger a shot only when we transition into frame 7 (index 6)
            # Assuming frame 7 in the filename loop (1 to 8) is index 6 in the list (0 to 7)
            if current_frame_idx == 6:
                self.should_fire = True
            else:
                self.should_fire = False
                
        else:
            self.should_fire = False # Ensure it's only true for a single frame update

        self.prev_frame_idx = current_frame_idx


class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_x: int, start_y: int, velocity: float = 5.0):
        super().__init__()
        script_base_dir = os.path.dirname(__file__)
        assets_dir_shot = os.path.join(script_base_dir, 'shot')
        shot_path = os.path.join(assets_dir_shot, 'sprite_shot.png')
        shot_img_raw = pygame.image.load(shot_path).convert_alpha()
        
        # Scale the projectile image
        scale_val = 3
        new_shot_size = (int(shot_img_raw.get_width() * scale_val), int(shot_img_raw.get_height() * scale_val))
        self.image = pygame.transform.smoothscale(shot_img_raw, new_shot_size)
        
        self.rect = self.image.get_rect()
        self.pos_x = float(start_x)
        self.rect.center = (int(self.pos_x), int(start_y))
        self.vel_x = float(velocity)

    def update(self):
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
    main_screen.fill(COLOR_BLACK)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
            
    # Update all sprites
    all_game_objects.update()
    
    # Check if the character should fire a shot
    if getattr(main_character, 'should_fire', False):
        y_pos_offset = -2  # slight upward adjustment
        # Spawn shot slightly to the right of the center
        shot_instance = Projectile(main_character.rect.centerx + 40, main_character.rect.centery + y_pos_offset)
        projectile_group.add(shot_instance)

    # Update and Draw all projectiles
    projectile_group.update()
    projectile_group.draw(main_screen)
    
    # Draw all game objects (including the main character)
    all_game_objects.draw(main_screen)
    
    # Update the display
    pygame.display.flip()
    
    # Cap the frame rate
    game_clock.tick(FPS)