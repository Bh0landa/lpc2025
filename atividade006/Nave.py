import sys
import math
import pygame

# Constants
WIDTH, HEIGHT = 1000, 800
FPS = 60
BACKGROUND_COLOR = (30, 30, 30)
TRIANGLE_COLOR = (255, 182, 193)
TRIANGLE_SIZE = 60
ROTATION_SPEED = 3
MOVEMENT_SPEED = 5
BREAK = 0

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

    def rotate(self, direction):
        # Adjust the triangle angle left or right.
        if direction == "left":
            self.angle = (self.angle - ROTATION_SPEED) % 360.0
        elif direction == "right":
            self.angle = (self.angle + ROTATION_SPEED) % 360.0

    def move(self, direction=None):
        # Move the triangle forward relative to its angle.
        angle_radians = math.radians(self.angle)
        dx = math.sin(angle_radians) * MOVEMENT_SPEED
        dy = -math.cos(angle_radians) * MOVEMENT_SPEED
        if BREAK == 0:
            # Continuous movement mode
            if direction == "forward":
                self.moving = True
            elif direction == "stop":
                self.moving = False

            if self.moving:
                self.position[0] += dx
                self.position[1] += dy
        else:
            # Momentary movement mode
            if direction == "forward":
                self.position[0] += dx
                self.position[1] += dy

def main():
    # Main loop.
    global BREAK
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rotating and Moving Triangle")
    clock = pygame.time.Clock()

    triangle = Triangle(position=(WIDTH // 2, HEIGHT // 2))

    running = True
    while running:
        clock.tick(FPS)
        screen.fill(BACKGROUND_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Detect keydown once to toggle BREAK when DOWN is pressed
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    BREAK = 1 - BREAK

        # Handle keyboard input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            triangle.rotate("left")
        if keys[pygame.K_RIGHT]:
            triangle.rotate("right")
        
        if keys[pygame.K_DOWN]:
            triangle.move("stop")

        if BREAK == 0:
            if keys[pygame.K_UP]:
                triangle.move("forward")
        else:
            # Momentary mode: move only while UP is pressed
            if keys[pygame.K_UP]:
                triangle.move("forward")

        triangle.move()

        # Draw the triangle
        pygame.draw.polygon(
            screen,
            TRIANGLE_COLOR,
            triangle.get_transformed_points(),
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()