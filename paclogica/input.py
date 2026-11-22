import pygame

DIRECTIONS = {
    pygame.K_UP: (-1,0), pygame.K_w: (-1,0),
    pygame.K_DOWN: (1,0), pygame.K_s: (1,0),
    pygame.K_LEFT: (0,-1), pygame.K_a: (0,-1),
    pygame.K_RIGHT: (0,1), pygame.K_d: (0,1),
}
ANSWER_KEYS = {
    pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3,
    pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2, pygame.K_KP4: 3,
}
CONFIRM_KEYS = {pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE}
PAUSE_KEYS = {pygame.K_ESCAPE, pygame.K_p}

def direction_for_key(key):
    return DIRECTIONS.get(key)

def answer_for_key(key):
    return ANSWER_KEYS.get(key)
