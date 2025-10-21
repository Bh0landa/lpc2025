import os
import sys
import pygame

HERE = os.path.dirname(__file__)
PARENT = os.path.abspath(os.path.join(HERE, '..'))
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

import core.core as core_mod
from core.core import GameState, WIDTH, HEIGHT, BACKGROUND_COLOR

FPS = 60


def get_aerplane_map(width, height):
    # No obstacles in airplane mode: fully open wrap-around space.
    return []


def draw_map(surface, walls, color=BACKGROUND_COLOR):
    # Draw obstacles. Default color hides them (same as background).
    for w in walls:
        pygame.draw.rect(surface, color, w)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Aerplane arena (lpc)')
    clock = pygame.time.Clock()

    state = GameState()
    # Use continuous movement only for aerplane mode.
    core_mod.BRAKE = 0

    # Start triangles moving and give opposite headings
    state.triangle1.moving = True
    state.triangle2.moving = True
    state.triangle1.angle = 0.0
    state.triangle2.angle = 180.0

    # simple clouds: two ovals side-by-side with alpha=100, centered
    # make clouds much larger and opaque so they cover a larger area
    cloud = pygame.Surface((720, 300), pygame.SRCALPHA)
    # left oval (slightly narrower)
    pygame.draw.ellipse(cloud, (255, 255, 255, 255), (0, 40, 320, 220))
    # right oval, moved right to increase gap between the two
    pygame.draw.ellipse(cloud, (255, 255, 255, 255), (400, 40, 320, 220))
    cloud_pos = (WIDTH // 2 - cloud.get_width() // 2, HEIGHT // 2 - cloud.get_height() // 2 - 40)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        screen.fill(BACKGROUND_COLOR)

        walls = get_aerplane_map(WIDTH, HEIGHT)
        draw_map(screen, walls)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # Pass rotation/forward/shoot to core
        state.handle_input(keys)

        # Move with wrap-around (no internal collisions)
        def wrap_entity(tri):
            tri.move()
            # wrap X
            if tri.position[0] < 0:
                tri.position[0] += WIDTH
            elif tri.position[0] > WIDTH:
                tri.position[0] -= WIDTH
            # wrap Y
            if tri.position[1] < 0:
                tri.position[1] += HEIGHT
            elif tri.position[1] > HEIGHT:
                tri.position[1] -= HEIGHT

        wrap_entity(state.triangle1)
        wrap_entity(state.triangle2)

        state.step()

        # Bullets disappear when leaving screen
        for t in (state.triangle1, state.triangle2):
            for b in list(t.bullets):
                if (
                    b['x'] < 0
                    or b['x'] > WIDTH
                    or b['y'] < 0
                    or b['y'] > HEIGHT
                ):
                    try:
                        t.bullets.remove(b)
                    except ValueError:
                        pass
                    continue
                pygame.draw.circle(
                    screen, (255, 255, 255), (int(b['x']), int(b['y'])), 3
                )

        state.draw(screen)
        # draw central cloud on top
        screen.blit(cloud, cloud_pos)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
