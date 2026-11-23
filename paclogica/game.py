import random
import math
import pygame
from .config import *
from .database import Database, Level, clean_name, MAX_NAME
from .effects import Effects
from .entities import Entity, Fruit
from .fonts import FontBook
from .layout import Layout, default_aspect
from .questions import make_question, TOPIC_NAMES
from .maze import free, create_dots, random_free_cell
from .input import direction_for_key, answer_for_key, CONFIRM_KEYS, PAUSE_KEYS
from .renderer import RendererMixin
from .scoring import Scoreboard, random_fruit, plural
from .audio import AudioManager

CAPTION = "Pac-Lógica — Lógica Proposicional"

def create_window(size, recreate=False):
    if recreate:
        # Trocar o tamanho de uma janela SCALED existente derruba o pygame-ce;
        # recriar o subsistema de vídeo é seguro.
        pygame.display.quit()
        pygame.display.init()
    pygame.display.set_caption(CAPTION)
    try:
        # SCALED deixa a janela redimensionável e nítida em telas HiDPI (Retina, 4K).
        return pygame.display.set_mode(size, pygame.SCALED | pygame.RESIZABLE)
    except pygame.error:
        return pygame.display.set_mode(size)

def arcade_level(wave, topics):
    return Level(
        number=wave, goal=0, dots=ARCADE_DOTS,
        ghosts=min(2 + (wave - 1) // 2, len(GHOST_STARTS)),
        ghost_step=max(ARCADE_GHOST_MIN_STEP, int(ARCADE_GHOST_STEP * .93 ** (wave - 1))),
        fruit_every=max(ARCADE_FRUIT_MIN_EVERY, ARCADE_FRUIT_EVERY - 600 * (wave - 1)),
        topics=topics)

def topic_names(level):
    return " · ".join(TOPIC_NAMES.get(t, t) for t in level.topic_list)

class PacLogica(RendererMixin):
    def __init__(self, db=None):
        # Só vídeo e fontes: o jogo não usa som nem joystick, que deixam a abertura lenta.
        pygame.display.init()
        pygame.font.init()
        self.db = db or Database()
        self.layout = Layout(self.db.get_setting("aspect") or default_aspect())
        self.screen = create_window(self.layout.size)
        self.clock = pygame.time.Clock()
        self.fonts = FontBook()
        self.audio = AudioManager()
        self.player_name = self.db.get_setting("player_name", "")
        self.effects = Effects()
        self.buttons = []
        self.ranking_mode = "arcade"
        self.last_score_id = self.last_rank = None
        self.mode = None
        self.running = True
        self._text_input_active = False
        self.prerender()
        self.state = "menu"

    # Partida e níveis
    def new_game(self, mode):
        self.player_name = clean_name(self.player_name)
        self.db.set_setting("player_name", self.player_name)
        self.mode = mode
        self.score = Scoreboard()
        self.hearts, self.revived = HEARTS, False
        self.level_no = 1
        self.last_score_id = self.last_rank = None
        self.audio.play("start")
        self.start_level()

    def start_level(self):
        if self.mode == "classic":
            self.level = self.db.level(self.level_no)
        else:
            # O arcade segue a mesma escala de questões dos níveis, sem metas.
            scale = self.db.level(min(self.level_no, self.db.level_count()))
            self.level = arcade_level(self.level_no, scale.topics)
        self.dots = create_dots(self.level.dots)
        self.eaten = 0
        self.fruit, self.fruit_timer = None, self.level.fruit_every
        self.score.new_level()
        self.effects.clear()
        self.reset_positions()
        self.inv = 1200
        title = f"NÍVEL {self.level_no}" if self.mode == "classic" else f"ONDA {self.level_no}"
        self.effects.announce(title, YELLOW, sub=topic_names(self.level))
        self.state = "play"

    def reset_positions(self):
        self.player = Entity(*PLAYER_START, PLAYER_STEP)
        self.ghosts = [Entity(r,c,self.level.ghost_step,color=col)
                       for r,c,col in GHOST_STARTS[:self.level.ghosts]]
        self.want = (0,0)
        self.inv = INVULN_MS

    def check_progress(self):
        """Depois de ganhar pontos: passa de nível ao atingir a meta ou repõe os docinhos."""
        if self.mode == "classic" and self.score.level_score >= self.level.goal:
            if self.level_no >= self.db.level_count():
                self.finish(victory=True)
            else:
                self.state = "level_up"
            return
        if not self.dots:
            if self.mode == "arcade":
                self.level_no += 1
                self.start_level()
            else:
                self.dots = create_dots(self.level.dots, {(self.player.r, self.player.c)})
                self.effects.announce("NOVOS DOCINHOS!", PURPLE)

    def next_level(self):
        self.level_no += 1
        self.hearts = HEARTS
        self.start_level()

    # Questões
    def ask(self, mode):
        self.question = make_question(self.level.topic_list)
        self.quiz_mode = mode
        self.quiz_left = QUIZ_TIME
        self.state = "quiz"
        self.feedback = None
        self.timed_out = False
        self.last_points = 0

    def answer(self, index):
        """Responde à questão; index None significa que o tempo acabou."""
        q = self.question
        if index is not None and index >= len(q["options"]): return
        self.timed_out = index is None
        ok = index == q["answer"]
        self.feedback = ok
        self.audio.play("correct" if ok else "wrong")
        if self.quiz_mode == "eat":
            if ok:
                self.last_points = self.score.correct_answer()
                x, y = self.player.pixel()
                self.effects.popup(f"+{plural(self.last_points, 'ponto')}", x, y - 10, GREEN, 26)
            else:
                self.score.wrong_answer()
        self.state = "feedback"

    def continue_after_feedback(self):
        mode, ok = self.quiz_mode, self.feedback
        if mode == "eat":
            if not ok:
                self.hearts -= 1
                self.audio.play("damage")
                if self.hearts <= 0:
                    self.lose()
                    return
        elif ok:
            self.revived = True
            self.hearts = REVIVE_HEARTS
            self.reset_positions()
        else:
            self.finish()
            return
        self.state = "play"
        self.check_progress()

    def lose(self):
        if self.revived:
            self.finish()
        else:
            self.ask("revive")

    def finish(self, victory=False):
        self.last_score_id, self.last_rank = self.db.save_score(
            self.player_name, self.mode, self.score.score, self.level_no)
        self.audio.play("victory" if victory else "game_over")
        self.ranking_mode = self.mode
        self.state = "victory" if victory else "over"

    # Movimento
    def step_player(self):
        p = self.player
        p.pr, p.pc = p.r, p.c
        wr,wc = self.want
        if (wr or wc) and free(p.r+wr,p.c+wc):
            p.dr,p.dc = wr,wc
        if free(p.r+p.dr,p.c+p.dc):
            p.r += p.dr; p.c += p.dc
        cell = r, c = (p.r,p.c)
        if self.fruit and cell == self.fruit.cell:
            self.eat_fruit()
            if self.state != "play": return
        if cell in self.dots:
            color = self.dots.pop(cell)
            self.audio.play("collect")
            self.eaten += 1
            self.effects.burst((c + .5) * TILE, (r + .5) * TILE, color, 10)
            self.ask("eat")

    def eat_fruit(self):
        kind = self.fruit.kind
        x, y = self.fruit.pixel()
        points = self.score.eat_fruit(kind)
        text = f"×{kind.multiplier}!" if kind.multiplier > 1 else f"+{plural(points, 'ponto')}"
        self.effects.popup(text, x, y - 12, kind.color, 30)
        self.effects.burst(x, y, kind.color, 24, .22)
        self.fruit, self.fruit_timer = None, self.level.fruit_every
        self.check_progress()

    def update_fruit(self, dt):
        if self.fruit:
            self.fruit.left -= dt
            if self.fruit.left <= 0:
                self.fruit, self.fruit_timer = None, self.level.fruit_every
            return
        self.fruit_timer -= dt
        if self.fruit_timer <= 0:
            player = (self.player.r, self.player.c)
            cell = random_free_cell(set(self.dots) | {player}, player, FRUIT_MIN_DISTANCE)
            if cell:
                self.fruit = Fruit(random_fruit(), cell, FRUIT_LIFETIME)
            self.fruit_timer = self.level.fruit_every

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
        self.effects.update(dt)
        if self.state == "quiz":
            self.quiz_left -= dt
            if self.quiz_left <= 0: self.answer(None)
            return
        if self.state != "play": return
        self.inv = max(0, self.inv-dt)
        self.score.tick(dt)
        self.update_fruit(dt)
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
                self.audio.play("damage")
                self.hearts -= 1
                self.score.streak = 0
                self.effects.burst(px, py, RED, 18)
                if self.hearts <= 0: self.lose()
                else: self.reset_positions()
                return

    # Tela
    def set_aspect(self, aspect):
        if aspect == self.layout.aspect: return
        self.layout = Layout(aspect)
        self.db.set_setting("aspect", self.layout.aspect)
        self.screen = create_window(self.layout.size, recreate=True)
        self.prerender()

    def toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            pass

    # Entrada
    def do(self, action):
        if action in ("classic", "arcade"): self.new_game(action)
        elif action == "again": self.new_game(self.mode)
        elif action == "menu": self.state = "menu"
        elif action == "ranking": self.state = "ranking"
        elif action == "quit": self.running = False
        elif action == "resume": self.state = "play"
        elif action == "pause": self.state = "pause"
        elif action == "next_level": self.next_level()
        elif action == "continue": self.continue_after_feedback()
        elif isinstance(action, tuple) and action[0] == "answer": self.answer(action[1])
        elif isinstance(action, tuple) and action[0] == "tab": self.ranking_mode = action[1]
        elif isinstance(action, tuple) and action[0] == "aspect": self.set_aspect(action[1])

    def on_key(self, event):
        key, state = event.key, self.state
        if key == pygame.K_F11:
            self.toggle_fullscreen()
        elif state == "play":
            direction = direction_for_key(key)
            if direction: self.want = direction
            elif key in PAUSE_KEYS: self.do("pause")
        elif state == "pause":
            if key in PAUSE_KEYS or key in CONFIRM_KEYS: self.do("resume")
        elif state == "quiz":
            index = answer_for_key(key)
            if index is not None: self.answer(index)
        elif state == "feedback":
            if key in CONFIRM_KEYS: self.do("continue")
        elif state == "level_up":
            if key in CONFIRM_KEYS: self.do("next_level")
        elif state in ("over", "victory"):
            if key in CONFIRM_KEYS: self.do("again")
            elif key == pygame.K_ESCAPE: self.do("menu")
        elif state == "ranking":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER): self.do("menu")
            elif key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                self.ranking_mode = "classic" if self.ranking_mode == "arcade" else "arcade"
        elif state == "menu":
            if key == pygame.K_BACKSPACE: self.player_name = self.player_name[:-1]

    def on_text(self, text):
        if self.state == "menu":
            text = "".join(ch for ch in text if ch.isprintable())
            self.player_name = (self.player_name + text)[:MAX_NAME]

    def handle_events(self):
        text_input_active = self.state == "menu"
        if text_input_active != self._text_input_active:
            if text_input_active:
                pygame.key.start_text_input()
            else:
                pygame.key.stop_text_input()
            self._text_input_active = text_input_active
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.KEYDOWN: self.on_key(event)
            elif event.type == pygame.TEXTINPUT: self.on_text(event.text)
            elif event.type == pygame.WINDOWFOCUSLOST and self.state == "play": self.do("pause")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, action in self.buttons:
                    if rect.collidepoint(event.pos):
                        self.do(action)
                        break

    def run(self):
        while self.running:
            # Limita o dt para evitar saltos ao arrastar a janela.
            dt = min(self.clock.tick(FPS), 100)
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        self.db.close()
        pygame.quit()

if __name__ == "__main__":
    PacLogica().run()
