
# Jucimar Jr
# 2024

import pygame
import math

pygame.init()

COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)

SCORE_MAX = 2

SIZE = (1280, 720)
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption("MyPong - PyGame Edition - 2024-09-02")

# Score text
score_font = pygame.font.Font('assets/PressStart2P.ttf', 44)
score_text = score_font.render('00 x 00', True, COLOR_WHITE, COLOR_BLACK)
score_text_rect = score_text.get_rect()
score_text_rect.center = (680, 50)

# Victory text
victory_font = pygame.font.Font('assets/PressStart2P.ttf', 100)
victory_text = victory_font.render('VICTORY', True, COLOR_WHITE, COLOR_BLACK)
victory_text_rect = score_text.get_rect()
victory_text_rect.center = (450, 350)

# Sound effects
try:
    bounce_sound_effect = pygame.mixer.Sound('assets/bounce.wav')
    scoring_sound_effect = pygame.mixer.Sound('assets/258020__kodack__arcade-bleep-sound.wav')
except Exception:
    bounce_sound_effect = None
    scoring_sound_effect = None

# Player 1
player_1 = pygame.image.load("assets/player.png")
player_1_y = 300
player_1_move_up = False
player_1_move_down = False

# Player 2 - robot
player_2 = pygame.image.load("assets/player.png")
player_2_y = 300

# Ball
ball = pygame.image.load("assets/ball.png")
ball_x = 640
ball_y = 360
ball_dx = 5
ball_dy = 5
BALL_SPEED = 7
BALL_ACCEL = 1.08
BALL_MAX_SPEED = 18

# Score
score_1 = 0
score_2 = 0

# Game loop
game_loop = True
game_clock = pygame.time.Clock()

def play_sound(sound):
    if sound:
        sound.play()

def reset_ball(direction=1):
    global ball_x, ball_y, ball_dx, ball_dy
    ball_x = 640
    ball_y = 360
    angle = math.radians(30)
    ball_dx = direction * BALL_SPEED * math.cos(angle)
    ball_dy = BALL_SPEED * math.sin(angle)

reset_ball()

while game_loop:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_loop = False
        # Keystroke events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                player_1_move_up = True
            if event.key == pygame.K_DOWN:
                player_1_move_down = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                player_1_move_up = False
            if event.key == pygame.K_DOWN:
                player_1_move_down = False

    # Checking the victory condition
    if score_1 < SCORE_MAX and score_2 < SCORE_MAX:
        # Clear screen
        screen.fill(COLOR_BLACK)


        # Ball collision with the wall
        if ball_y > 700:
            ball_y = 700
            ball_dy *= -1
            play_sound(bounce_sound_effect)
        elif ball_y <= 0:
            ball_y = 0
            ball_dy *= -1
            play_sound(bounce_sound_effect)

        # Ball collision with player 1's paddle
        if 50 < ball_x < 100:
            if player_1_y < ball_y + 25 and player_1_y + 150 > ball_y:
                # Calcula o ponto de contato
                rel_y = (ball_y + 25) - (player_1_y + 75)
                norm_rel_y = rel_y / 75
                bounce_angle = norm_rel_y * (math.pi / 3)  # até 60 graus
                speed = min(math.hypot(ball_dx, ball_dy) * BALL_ACCEL, BALL_MAX_SPEED)
                ball_dx = speed * math.cos(bounce_angle)
                ball_dy = speed * math.sin(bounce_angle)
                if ball_dx < 0:
                    ball_dx *= -1
                play_sound(bounce_sound_effect)

        # Ball collision with player 2's paddle
        if 1160 < ball_x < 1210:
            if player_2_y < ball_y + 25 and player_2_y + 150 > ball_y:
                rel_y = (ball_y + 25) - (player_2_y + 75)
                norm_rel_y = rel_y / 75
                bounce_angle = norm_rel_y * (math.pi / 3)
                speed = min(math.hypot(ball_dx, ball_dy) * BALL_ACCEL, BALL_MAX_SPEED)
                ball_dx = -abs(speed * math.cos(bounce_angle))
                ball_dy = speed * math.sin(bounce_angle)
                play_sound(bounce_sound_effect)

        # Scoring points
        if ball_x < -50:
            reset_ball(direction=1)
            score_2 += 1
            play_sound(scoring_sound_effect)
        elif ball_x > 1320:
            reset_ball(direction=-1)
            score_1 += 1
            play_sound(scoring_sound_effect)

        # Ball movement
        ball_x += ball_dx
        ball_y += ball_dy

        # Player 1 up movement
        if player_1_move_up:
            player_1_y -= 5
        # Player 1 down movement
        if player_1_move_down:
            player_1_y += 5

        # Player 1 collides with upper wall
        if player_1_y <= 0:
            player_1_y = 0
        # Player 1 collides with lower wall
        elif player_1_y >= 570:
            player_1_y = 570

        # Player 2 "Artificial Intelligence" (segue suavemente a bola)
        if player_2_y + 75 < ball_y + 25:
            player_2_y += min(5, (ball_y + 25) - (player_2_y + 75))
        elif player_2_y + 75 > ball_y + 25:
            player_2_y -= min(5, (player_2_y + 75) - (ball_y + 25))
        # Limites da raquete 2
        if player_2_y <= 0:
            player_2_y = 0
        elif player_2_y >= 570:
            player_2_y = 570

        # Update score hud
        score_text = score_font.render(f'{score_1} x {score_2}', True, COLOR_WHITE, COLOR_BLACK)

        # Drawing objects
        screen.blit(ball, (ball_x, ball_y))
        screen.blit(player_1, (50, player_1_y))
        screen.blit(player_2, (1180, player_2_y))
        screen.blit(score_text, score_text_rect)
    else:
        # Drawing victory
        screen.fill(COLOR_BLACK)
        screen.blit(score_text, score_text_rect)
        screen.blit(victory_text, victory_text_rect)

    # Update screen
    pygame.display.flip()
    game_clock.tick(60)

pygame.quit()