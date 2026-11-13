import random
import math
import pygame
from .config import *
from .entities import Entity
from .logic import make_question
from .maze import free, create_dots
from .input import direction_for_key
from .renderer import RendererMixin

class PacLogica(RendererMixin):
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pac-Lógica — Lógica Proposicional")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT + HUD_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 22)
        self.small = pygame.font.SysFont("arial", 17)
        self.big = pygame.font.SysFont("arial", 30, bold=True)
        self.state = "menu"
        self.message = "Coma os docinhos e responda às questões de lógica!"
        self.reset_game()

    def reset_game(self):
        self.hearts, self.eaten, self.revived = HEARTS, 0, False
        self.dots = create_dots()
        self.player = Entity(*PLAYER_START, PLAYER_STEP)
        self.ghosts = [Entity(r,c,GHOST_STEP,color=col) for r,c,col in GHOST_STARTS]
        self.want = (0,0)
        self.inv = 1200
        self.state = "play"

    def reset_positions(self):
        self.player = Entity(*PLAYER_START, PLAYER_STEP)
        self.ghosts = [Entity(r,c,GHOST_STEP,color=col) for r,c,col in GHOST_STARTS]
        self.want = (0,0)
        self.inv = INVULN_MS

    def ask(self, mode):
        self.question = make_question()
        self.quiz_mode = mode
        self.state = "quiz"
        self.feedback = None

    def answer(self, index):
        q = self.question
        ok = index == q["answer"]
        self.feedback = ok
        self.state = "feedback"

    def continue_after_feedback(self):
        q, mode, ok = self.question, self.quiz_mode, self.feedback
        if mode == "eat":
            if not ok:
                self.hearts -= 1
                if self.hearts <= 0:
                    self.lose()
                    return
        elif ok:
            self.revived = True
            self.hearts = REVIVE_HEARTS
            self.reset_positions()
        else:
            self.game_over()
            return
        if self.eaten >= TOTAL_DOTS:
            self.state = "win"
        else:
            self.state = "play"

    def lose(self):
        if self.revived:
            self.game_over()
        else:
            self.ask("revive")

    def game_over(self):
        self.state = "over"

    def step_player(self):
        p = self.player
        p.pr, p.pc = p.r, p.c
        wr,wc = self.want
        if (wr or wc) and free(p.r+wr,p.c+wc):
            p.dr,p.dc = wr,wc
        if free(p.r+p.dr,p.c+p.dc):
            p.r += p.dr; p.c += p.dc
        cell = (p.r,p.c)
        if cell in self.dots:
            del self.dots[cell]
            self.eaten += 1
            self.ask("eat")

    def step_ghost(self, e):
        p = self.player
        moves = [(0,1),(0,-1),(1,0),(-1,0)]
        all_moves = [d for d in moves if free(e.r+d[0],e.c+d[1])]
        opts = [d for d in all_moves if d != (-e.dr,-e.dc)] or all_moves
        if not opts: return
        if random.random() < GHOST_CHASE:
            d = min(opts, key=lambda x: abs(e.r+x[0]-p.r)+abs(e.c+x[1]-p.c))
        else:
            d = random.choice(opts)
        e.dr,e.dc = d
        e.pr,e.pc = e.r,e.c
        e.r += d[0]; e.c += d[1]

    def update(self, dt):
        if self.state != "play": return
        self.inv = max(0, self.inv-dt)
        self.player.acc += dt
        while self.player.acc >= self.player.step and self.state == "play":
            self.player.acc -= self.player.step
            self.step_player()
        if self.state != "play": return
        for ghost in self.ghosts:
            ghost.acc += dt
            while ghost.acc >= ghost.step:
                ghost.acc -= ghost.step
                self.step_ghost(ghost)
        if self.inv > 0: return
        px,py = self.player.pixel()
        for ghost in self.ghosts:
            gx,gy = ghost.pixel()
            if math.hypot(px-gx,py-gy) < TILE*.6:
                self.hearts -= 1
                if self.hearts <= 0: self.lose()
                else: self.reset_positions()
                return

    def run(self):
        running=True
        while running:
            dt=self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running=False
                elif event.type == pygame.KEYDOWN:
                    direction = direction_for_key(event.key)
                    if direction and self.state == "play":
                        self.want = direction
                    if event.key==pygame.K_ESCAPE and self.state=="play": self.state="menu"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                    if self.state in ("menu","quiz","feedback","over","win"):
                        pos=event.pos
                        for rect,action in getattr(self,"button_rects",[]):
                            if rect.collidepoint(pos):
                                if action=="start" or action=="restart": self.reset_game()
                                elif isinstance(action,int): self.answer(action)
                                elif action=="continue": self.continue_after_feedback()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    PacLogica().run()
