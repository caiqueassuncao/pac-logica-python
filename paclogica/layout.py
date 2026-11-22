import pygame
from .config import ASPECTS, ROWS, COLS

class Layout:
    """Posição do labirinto e do HUD para cada proporção de tela.

    4:3  → labirinto centralizado com o HUD embaixo.
    16:9 → labirinto maior à esquerda com um painel lateral.
    """

    def __init__(self, aspect):
        self.aspect = aspect if aspect in ASPECTS else "16:9"
        self.w, self.h = self.size = ASPECTS[self.aspect]
        self.side = self.aspect == "16:9"
        if self.side:
            self.tile = 40
            self.world = pygame.Rect(20, (self.h - ROWS*self.tile)//2, COLS*self.tile, ROWS*self.tile)
            self.hud = pygame.Rect(self.world.right + 20, self.world.y, self.w - self.world.right - 40, self.world.h)
        else:
            self.tile = 36
            self.world = pygame.Rect((self.w - COLS*self.tile)//2, 8, COLS*self.tile, ROWS*self.tile)
            self.hud = pygame.Rect(16, self.world.bottom + 8, self.w - 32, self.h - self.world.bottom - 16)

def default_aspect():
    """16:9 em monitores largos, 4:3 nos demais."""
    try:
        w, h = pygame.display.get_desktop_sizes()[0]
        return "16:9" if w / h >= 1.5 else "4:3"
    except (pygame.error, IndexError, ZeroDivisionError):
        return "16:9"
