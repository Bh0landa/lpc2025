# Configurações do jogo
# Valores usados por vários módulos para controlar o comportamento
# e a aparência do jogo
# Screen
WIDTH = 920
HEIGHT = 700
FPS = 60

# Parâmetros gerais do jogo como vidas e tempos entre eventos
# Game
START_LIVES = 3
SAFE_SPAWN_TIME = 2.0  # seconds of invulnerability after respawn
WAVE_DELAY = 2.0       # seconds between waves

# Parâmetros para o funcionamento da nave do jogador
# Ship
SHIP_RADIUS = 15
SHIP_TURN_SPEED = 220.0  # deg/s
SHIP_THRUST = 220.0      # px/s^2
SHIP_SPEED = 220.0       # px/s velocidade de movimento controlada por teclas (W/A/S/D)
SHIP_FRICTION = 0.995
SHIP_FIRE_RATE = 0.2     # seconds between shots
SHIP_BULLET_SPEED = 420.0
HYPERSPACE_COST = 250    # negative points cost for hyperspace
# Pixel-art scale for the player sprite (integer). Use 1..4 depending on desired size.
SHIP_PIXEL_SCALE = 3

# Tamanhos, pontuação e comportamento de fragmentação
# Asteroids
AST_VEL_MIN = 30.0
AST_VEL_MAX = 90.0
AST_SIZES = {
    "L": {"r": 46, "score": 20, "split": ["M", "M"]},
    "M": {"r": 24, "score": 50, "split": ["S", "S"]},
    "S": {"r": 12, "score": 100, "split": []},
}

# Bullet
BULLET_RADIUS = 2
BULLET_TTL = 1.0
BULLET_SPEED = 800.0  # velocidade das balas (px/s)

# Parâmetros de aparecimento e comportamento das naves inimigas
# UFO
UFO_SPAWN_EVERY = 15.0  # seconds
UFO_SPEED = 80.0
UFO_BIG = {"r": 18, "score": 200, "aim": 0.2}
UFO_SMALL = {"r": 12, "score": 1000, "aim": 0.6}

# Colors (R, G, B)
WHITE = (240, 240, 240)
GRAY = (120, 120, 120)
BLACK = (0, 0, 0)

# Definir um inteiro aqui para reproduzir runs quando precisar
# Randomness
RANDOM_SEED = None  # or set an int for reproducibility