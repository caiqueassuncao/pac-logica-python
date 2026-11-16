ROWS, COLS, TILE = 17, 23, 36
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE
HUD_HEIGHT = 96
SCREEN_W, SCREEN_H = WIDTH, HEIGHT + HUD_HEIGHT
FPS = 60
MAP = [
    '#######################',
    '#.....................#',
    '#..##.....###.....##..#',
    '#.....................#',
    '#.....................#',
    '#....##.........##....#',
    '#.....................#',
    '#.....................#',
    '#..##.....###.....##..#',
    '#.....................#',
    '#.....................#',
    '#.....##.......##.....#',
    '#.....................#',
    '#.....................#',
    '#..##.....##......##..#',
    '#.....................#',
    '#######################'
]

PLAYER_START = (15, 11)
# Os níveis usam os primeiros N fantasmas desta lista.
GHOST_STARTS = [
    (1, 1, (255, 77, 109)),
    (1, 21, (76, 201, 240)),
    (1, 11, (255, 140, 220)),
    (15, 1, (255, 170, 60)),
]
HEARTS, REVIVE_HEARTS = 3, 2
PLAYER_STEP = 145
GHOST_CHASE, INVULN_MS = 0.52, 1800
VARIABLES = ["p", "q"]
OPS = ["∧", "∨", "→", "↔"]
CANDY_COLORS = [(255,126,182),(122,252,255),(254,255,156),(178,141,255),(125,255,179)]

# Pontuação: cada docinho vale 1 ponto quando a questão é respondida corretamente.
CANDY_POINTS = 1
QUIZ_TIME = 15000

# Frutas especiais
FRUIT_LIFETIME, FRUIT_BLINK = 9000, 2500
FRUIT_MIN_DISTANCE = 4

# Modo arcade: sem metas, cada labirinto limpo inicia uma onda mais difícil.
ARCADE_DOTS = 12
ARCADE_GHOST_STEP, ARCADE_GHOST_MIN_STEP = 285, 170
ARCADE_FRUIT_EVERY, ARCADE_FRUIT_MIN_EVERY = 12000, 7000

MODE_NAMES = {"classic": "Tradicional", "arcade": "Arcade"}

# Paleta
BG_TOP=(12,10,42); BG_BOTTOM=(26,8,52)
WALL_FILL=(14,16,60); NEON=(70,110,255); NEON_SOFT=(140,120,255)
PANEL=(20,22,66); PANEL_EDGE=(95,110,255)
ACCENT=(72,92,230); GOOD_BTN=(36,160,110); BAD_BTN=(190,60,90)
YELLOW=(255,210,63); WHITE=(245,247,255); MUTED=(170,180,210)
GREEN=(90,230,150); RED=(255,100,120); ORANGE=(255,160,60); PURPLE=(180,120,255)
