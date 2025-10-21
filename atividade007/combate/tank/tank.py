import os
import sys
import pygame

# Make sure the parent folder (combate) is importable so we can import core
HERE = os.path.dirname(__file__)
PARENT = os.path.abspath(os.path.join(HERE, '..'))
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from core.core import WIDTH, HEIGHT, BACKGROUND_COLOR, GameState


def get_atari_map(width, height):
    walls = []
    margin = 30
    wall_thickness = 15

    # Outer borders
    walls.append(pygame.Rect(0, 0, width, margin))
    walls.append(pygame.Rect(0, height - margin, width, margin))
    walls.append(pygame.Rect(0, 0, margin, height))
    walls.append(pygame.Rect(width - margin, 0, margin, height))

    # Central vertical pair with a gap
    center_wall_w = 20
    center_wall_h = 150
    center_gap = 180
    walls.append(pygame.Rect(width//2 - center_gap//2 - center_wall_w, height//2 - center_wall_h//2, center_wall_w, center_wall_h))
    walls.append(pygame.Rect(width//2 + center_gap//2, height//2 - center_wall_h//2, center_wall_w, center_wall_h))

    # Side U-shaped obstacles
    side_wall_h = 200
    side_wall_w = 80
    side_offset_x = 150
    # Left U
    walls.append(pygame.Rect(side_offset_x, height//2 - side_wall_h//2, side_wall_w, wall_thickness))
    walls.append(pygame.Rect(side_offset_x, height//2 + side_wall_h//2 - wall_thickness, side_wall_w, wall_thickness))
    walls.append(pygame.Rect(side_offset_x, height//2 - side_wall_h//2, wall_thickness, side_wall_h))
    # Right U
    walls.append(pygame.Rect(width - side_offset_x - side_wall_w, height//2 - side_wall_h//2, side_wall_w, wall_thickness))
    walls.append(pygame.Rect(width - side_offset_x - side_wall_w, height//2 + side_wall_h//2 - wall_thickness, side_wall_w, wall_thickness))
    walls.append(pygame.Rect(width - side_offset_x - wall_thickness, height//2 - side_wall_h//2, wall_thickness, side_wall_h))

    # Corner L-shaped obstacles
    corner_wall_len = 100
    corner_offset = 120
    # Top-left
    walls.append(pygame.Rect(corner_offset, corner_offset, corner_wall_len, wall_thickness))
    walls.append(pygame.Rect(corner_offset, corner_offset, wall_thickness, corner_wall_len))
    # Top-right
    walls.append(pygame.Rect(width - corner_offset - corner_wall_len, corner_offset, corner_wall_len, wall_thickness))
    walls.append(pygame.Rect(width - corner_offset - wall_thickness, corner_offset, wall_thickness, corner_wall_len))
    # Bottom-left
    walls.append(pygame.Rect(corner_offset, height - corner_offset - wall_thickness, corner_wall_len, wall_thickness))
    walls.append(pygame.Rect(corner_offset, height - corner_offset - corner_wall_len, wall_thickness, corner_wall_len))
    # Bottom-right
    walls.append(pygame.Rect(width - corner_offset - corner_wall_len, height - corner_offset - wall_thickness, corner_wall_len, wall_thickness))
    walls.append(pygame.Rect(width - corner_offset - wall_thickness, height - corner_offset - corner_wall_len, wall_thickness, corner_wall_len))

    return walls


def draw_map(surface, walls, color=(205, 179, 128)):
    for w in walls:
        pygame.draw.rect(surface, color, w)

FPS = 60


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Tank arena (lpc)')
    clock = pygame.time.Clock()

    # create game state (triangles, bullets, scores)
    state = GameState()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        screen.fill(BACKGROUND_COLOR)

        # draw map
        walls = get_atari_map(WIDTH, HEIGHT)
        draw_map(screen, walls)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # pass keys to shared game state for handling
        state.handle_input(keys)

        if keys[pygame.K_s]:
            state.triangle1.move('backward')
        else:
            # if not holding S, and BRAKE is continuous, ensure moving_back flag cleared
            state.triangle1.move('stop') if not keys[pygame.K_w] and not state.triangle1.moving else None

        if keys[pygame.K_DOWN]:
            state.triangle2.move('backward')
        else:
            state.triangle2.move('stop') if not keys[pygame.K_UP] and not state.triangle2.moving else None

        def resolve_collision(tri):
            tri.move()
            # if triangle is invincible, skip collision resolution so it can pass through
            # internal walls, but still enforce window bounds (cannot leave the screen)
            if getattr(tri, 'is_invincible', False):
                tri.position[0] = max(0, min(WIDTH, tri.position[0]))
                tri.position[1] = max(0, min(HEIGHT, tri.position[1]))
                return
            for _ in range(3):
                collided = False
                for w in walls:
                    coll, mx, my = tri.collides_with_rect(w)
                    if coll:
                        PAD = 1.5
                        tri.position[0] += mx + (mx / (abs(mx)+1e-6)) * PAD if mx != 0 else 0
                        tri.position[1] += my + (my / (abs(my)+1e-6)) * PAD if my != 0 else 0
                        collided = True
                if not collided:
                    break
            # clamp to window bounds as safety
            tri.position[0] = max(0, min(WIDTH, tri.position[0]))
            tri.position[1] = max(0, min(HEIGHT, tri.position[1]))

        # resolve collisions for each triangle stored in state
        resolve_collision(state.triangle1)
        resolve_collision(state.triangle2)

        # advance shared game state (bullets, cooldowns, score detection)
        state.step()

        # remove bullets that collide with walls and draw remaining bullets
        for t in (state.triangle1, state.triangle2):
            for b in list(t.bullets):
                brect = pygame.Rect(int(b['x']) - 3, int(b['y']) - 3, 6, 6)
                hit = False
                for w in walls:
                    if w.colliderect(brect):
                        try:
                            t.bullets.remove(b)
                        except ValueError:
                            pass
                        hit = True
                        break
                if not hit:
                    pygame.draw.circle(screen, (255,255,255), (int(b['x']), int(b['y'])), 3)

        # draw everything from GameState (triangles + scores + bullets already drawn above)
        state.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
