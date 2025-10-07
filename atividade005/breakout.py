import pygame
import sys

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
BRICK_ROWS = 5
BRICK_COLS = 10
BRICK_WIDTH = WIDTH // BRICK_COLS
BRICK_HEIGHT = 30
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 15
BALL_RADIUS = 10

class Paddle:
	def __init__(self):
		self.rect = pygame.Rect(
			(WIDTH - PADDLE_WIDTH) // 2,
			HEIGHT - 40,
			PADDLE_WIDTH,
			PADDLE_HEIGHT
		)
		self.speed = 7

	def move(self, direction):
		if direction == 'left':
			self.rect.x -= self.speed
		elif direction == 'right':
			self.rect.x += self.speed
		self.rect.x = max(0, min(WIDTH - PADDLE_WIDTH, self.rect.x))

	def draw(self, surface):
		pygame.draw.rect(surface, (255, 255, 255), self.rect)

class Brick:
	def __init__(self, x, y, color):
		self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
		self.color = color
		self.alive = True

	def draw(self, surface):
		if self.alive:
			pygame.draw.rect(surface, self.color, self.rect)


def create_bricks():
	bricks = []
	# Classic Breakout colors
	colors = [
		(255, 0, 0),      # Red
		(255, 165, 0),    # Orange
		(255, 255, 0),    # Yellow
		(0, 128, 0),      # Green
		(0, 0, 255)       # Blue
	]
	for row in range(BRICK_ROWS):
		for col in range(BRICK_COLS):
			x = col * BRICK_WIDTH
			y = row * BRICK_HEIGHT + 60
			color = colors[row % len(colors)]
			bricks.append(Brick(x, y, color))
	return bricks

class Ball:

	def __init__(self):
		self.x = WIDTH // 2
		self.y = HEIGHT // 2
		self.dx = 5
		self.dy = -5

	def move(self):
		self.x += self.dx
		self.y += self.dy
		if self.x <= BALL_RADIUS or self.x >= WIDTH - BALL_RADIUS:
			self.dx *= -1
		if self.y <= BALL_RADIUS:
			self.dy *= -1

	def draw(self, surface):
		pygame.draw.circle(surface, (255, 255, 255), (self.x, self.y), BALL_RADIUS)

	def get_rect(self):
		return pygame.Rect(self.x - BALL_RADIUS, self.y - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)

#main function
def main():
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Breakout")
	clock = pygame.time.Clock()

	paddle = Paddle()
	ball = Ball()
	bricks = create_bricks()
	lives = 3
	score = 0
	font = pygame.font.SysFont(None, 36)

	running = True
	game_over = False
	win = False
	while running:
		clock.tick(FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

		if not game_over:
			keys = pygame.key.get_pressed()
			if keys[pygame.K_LEFT]:
				paddle.move('left')
			if keys[pygame.K_RIGHT]:
				paddle.move('right')

			ball.move()

			# Ball and paddle collision
			if ball.get_rect().colliderect(paddle.rect):
				ball.dy *= -1
				# Bounce the ball according to the position on the paddle
				offset = (ball.x - paddle.rect.centerx) / (PADDLE_WIDTH // 2)
				ball.dx = int(7 * offset)
				ball.y = paddle.rect.y - BALL_RADIUS

			# Ball and brick collision
			for brick in bricks:
				if brick.alive and ball.get_rect().colliderect(brick.rect):
					brick.alive = False
					score += 10
					# Bounce the ball correctly
					if abs(ball.x - brick.rect.left) < BALL_RADIUS or abs(ball.x - brick.rect.right) < BALL_RADIUS:
						ball.dx *= -1
					else:
						ball.dy *= -1
					break

			# Ball out of bounds
			if ball.y > HEIGHT:
				game_over = True

			# Win condition
			if all(not brick.alive for brick in bricks):
				win = True
				game_over = True

		screen.fill((0, 0, 0))
		paddle.draw(screen)
		ball.draw(screen)
		for brick in bricks:
			brick.draw(screen)

		# Draw score only
		score_text = font.render(f"Score: {score}", True, (255, 255, 255))
		screen.blit(score_text, (10, 10))

		# Draw game over or win
		if game_over:
			if win:
				msg = "YOU WIN!"
			else:
				msg = "GAME OVER"
			msg_text = font.render(msg, True, (255, 255, 255))
			screen.blit(msg_text, (WIDTH // 2 - msg_text.get_width() // 2, HEIGHT // 2))
			keys = pygame.key.get_pressed()
			if keys[pygame.K_ESCAPE]:
				running = False

		pygame.display.flip()

	pygame.quit()
	sys.exit()


if __name__ == "__main__":
	main()