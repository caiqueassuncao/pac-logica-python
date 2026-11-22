# TILE é a unidade lógica do jogo; na tela cada proporção desenha o labirinto no próprio tamanho.
ROWS, COLS, TILE = 17, 23, 36
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE
ASPECTS = {"4:3": (960, 720), "16:9": (1280, 720)}
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
BG_TOP=(16,14,40); BG_BOTTOM=(24,15,46)
WALL_FILL=(22,24,64); NEON=(112,132,255); NEON_SOFT=(150,128,240)
PANEL=(24,26,62); PANEL_EDGE=(104,118,230)
ACCENT=(86,98,206); GOOD_BTN=(44,148,112); BAD_BTN=(170,70,98)
YELLOW=(255,212,92); WHITE=(236,239,250); MUTED=(158,166,200)
GREEN=(108,224,160); RED=(255,112,130); ORANGE=(255,168,82); PURPLE=(178,132,255)
