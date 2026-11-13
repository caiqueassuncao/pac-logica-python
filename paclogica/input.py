import pygame

DIRECTIONS = {
    pygame.K_UP: (-1,0), pygame.K_w: (-1,0),
    pygame.K_DOWN: (1,0), pygame.K_s: (1,0),
    pygame.K_LEFT: (0,-1), pygame.K_a: (0,-1),
    pygame.K_RIGHT: (0,1), pygame.K_d: (0,1),
}

def direction_for_key(key):
    return DIRECTIONS.get(key)
