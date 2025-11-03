import os
import pygame
from pygame.locals import *
from sys import exit

pygame.init()

# Window size
WIDTH = 640
HEIGHT = 480
# Colors
BLACK = (0, 0, 0)

# Main display surface
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Mega Man X')

class MegaManX(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        script_dir = os.path.dirname(__file__)
        assets_dir = os.path.join(script_dir, 'mega_man')

        self.sprites: list[pygame.Surface] = []
        scale_factor = 3.0

        for i in range(1, 22):
            filename = f'sprite_{i}.png'
            path = os.path.join(assets_dir, filename)
            img: pygame.Surface = pygame.image.load(path).convert_alpha()
            w, h = img.get_size()
            new_size = (int(w * scale_factor), int(h * scale_factor))
            img = pygame.transform.smoothscale(img, new_size)
            self.sprites.append(img)

        # animation state
        self.current = 0.0
        self.image: pygame.Surface = self.sprites[int(self.current)]
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)

        # used to detect transition into the shot frame
        self.prev_frame = -1
        self.spawn_shot = False

    def update(self):
        # advance animation (float index)
        self.current += 0.008
        if self.current >= len(self.sprites):
            self.current = 0.0
        old_center = self.rect.center
        self.image = self.sprites[int(self.current)]
        self.rect = self.image.get_rect()
        self.rect.center = old_center
        current_frame = int(self.current)
        # trigger a shot only when we transition into frame 20
        if current_frame != self.prev_frame and current_frame == 20:
            self.spawn_shot = True
        else:
            self.spawn_shot = False
        self.prev_frame = current_frame


class Shot(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, speed: float = 0.7):
        super().__init__()
        script_dir = os.path.dirname(__file__)
        assets_dir = os.path.join(script_dir, 'shot')
        shot_path = os.path.join(assets_dir, 'sprite_shot.png')
        img = pygame.image.load(shot_path).convert_alpha()
        self.image = pygame.transform.smoothscale(img, (int(img.get_width() * 3), int(img.get_height() * 3)))
        self.rect = self.image.get_rect()
        self.x = float(x)
        self.rect.center = (int(self.x), int(y))
        self.vx = float(speed)

    def update(self):
        self.x += self.vx
        self.rect.x = int(self.x)
        if self.rect.left > WIDTH or self.rect.right < 0:
            self.kill()

all_sprites = pygame.sprite.Group()
player = MegaManX()
all_sprites.add(player)
shots_group = pygame.sprite.Group()

while True:
    screen.fill(BLACK)
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()

    all_sprites.draw(screen)
    all_sprites.update()

    if getattr(player, 'spawn_shot', False):
        y_offset = -2  # slight upward offset
        shot = Shot(player.rect.centerx + 40, player.rect.centery + y_offset)
        shots_group.add(shot)

    shots_group.update()
    shots_group.draw(screen)
    pygame.display.flip()