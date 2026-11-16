import math
import random
from datetime import datetime
import pygame
from .config import *
from .questions import TOPIC_NAMES
from .scoring import FRUITS, plural

def mix(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))

def lighten(c, t): return mix(c, (255,255,255), t)
def darken(c, t): return mix(c, (0,0,0), t)

def blur(surf, factor):
    w, h = surf.get_size()
    small = pygame.transform.smoothscale(surf, (max(1, w//factor), max(1, h//factor)))
    return pygame.transform.smoothscale(small, (w, h))

def thousands(n):
    return f"{n:,}".replace(",", ".")

CX = SCREEN_W // 2

class RendererMixin:
    # Recursos pré-renderizados
    def prerender(self):
        self._cache = {}
        self._hand = None
        self.mouse = (0, 0)
        self.background = self.make_background()
        self.maze_surface = self.make_maze()

    def make_background(self):
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            pygame.draw.line(surf, mix(BG_TOP, BG_BOTTOM, y/SCREEN_H), (0,y), (SCREEN_W,y))
        rng = random.Random(7)
        for _ in range(110):
            c = rng.randint(50, 110)
            surf.set_at((rng.randrange(SCREEN_W), rng.randrange(SCREEN_H)), (c, c, min(255, c+50)))
        return surf

    def make_maze(self):
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        lines = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        lines.fill((*NEON, 0))
        inner = pygame.Rect(TILE, TILE, WIDTH-2*TILE, HEIGHT-2*TILE).inflate(8, 8)
        surf.fill((*WALL_FILL, 255))
        pygame.draw.rect(surf, (0,0,0,0), inner, border_radius=16)
        pygame.draw.rect(lines, (*NEON, 255), inner, 3, border_radius=16)
        pygame.draw.rect(lines, (*NEON_SOFT, 190), surf.get_rect().inflate(-12,-12), 2, border_radius=20)
        # Paredes internas como blocos arredondados por trecho horizontal.
        for r in range(1, ROWS-1):
            c = 1
            while c < COLS-1:
                if MAP[r][c] != "#":
                    c += 1
                    continue
                start = c
                while c < COLS-1 and MAP[r][c] == "#": c += 1
                rect = pygame.Rect(start*TILE+5, r*TILE+6, (c-start)*TILE-10, TILE-12)
                pygame.draw.rect(surf, (*WALL_FILL, 255), rect, border_radius=10)
                pygame.draw.rect(lines, (*NEON, 255), rect, 3, border_radius=10)
        glow = blur(lines, 6)
        surf.blit(glow, (0,0)); surf.blit(glow, (0,0))
        surf.blit(lines, (0,0))
        return surf

    def glow(self, color, radius, strength=110):
        key = ("glow", color, radius, strength)
        if key not in self._cache:
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            for i in range(radius, 0, -1):
                pygame.draw.circle(s, (*color, int(strength * (1 - i/radius)**2)), (radius, radius), i)
            self._cache[key] = s
        return self._cache[key]

    def blit_glow(self, color, x, y, radius, strength=110):
        self.screen.blit(self.glow(color, radius, strength), (x-radius, y-radius))

    def dim(self, alpha=170):
        key = ("dim", alpha)
        if key not in self._cache:
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            s.fill((5, 5, 20, alpha))
            self._cache[key] = s
        self.screen.blit(self._cache[key], (0,0))

    # Texto
    def text(self, s, pos, size=20, color=WHITE, bold=False, anchor="topleft", alpha=255):
        font, s = self.fonts.prepare(str(s), size, bold)
        surf = font.render(s, True, color)
        if alpha < 255: surf.set_alpha(max(0, alpha))
        rect = surf.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
        self.screen.blit(surf, rect)
        return rect

    def text_width(self, s, size, bold=False):
        font, s = self.fonts.prepare(str(s), size, bold)
        return font.size(s)[0]

    def glow_text(self, s, pos, size, color, anchor="center"):
        key = ("gtext", s, size, color)
        if key not in self._cache:
            font, s2 = self.fonts.prepare(s, size, True)
            surf = font.render(s2, True, color)
            pad = size // 2
            g = pygame.Surface((surf.get_width()+2*pad, surf.get_height()+2*pad), pygame.SRCALPHA)
            g.fill((*color, 0))
            g.blit(surf, (pad, pad))
            self._cache[key] = (surf, blur(g, 5), pad)
        surf, glow, pad = self._cache[key]
        rect = surf.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
        self.screen.blit(glow, rect.move(-pad, -pad)); self.screen.blit(glow, rect.move(-pad, -pad))
        self.screen.blit(surf, rect)
        return rect

    def wrap(self, s, size, max_width):
        lines, line = [], ""
        for word in s.split():
            test = (line + " " + word).strip()
            if self.text_width(test, size) <= max_width: line = test
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
        return lines

    def paragraph(self, s, pos, size, max_width, color=WHITE, anchor="midtop", spacing=6):
        x, y = pos
        for line in self.wrap(s, size, max_width):
            r = self.text(line, (x, y), size, color, anchor=anchor)
            y += r.height + spacing
        return y

    # Componentes
    def panel(self, rect, accent=PANEL_EDGE):
        rect = pygame.Rect(rect)
        key = ("panel", rect.size, accent)
        if key not in self._cache:
            pad = 24
            g = pygame.Surface((rect.w+2*pad, rect.h+2*pad), pygame.SRCALPHA)
            g.fill((*accent, 0))
            pygame.draw.rect(g, (*accent, 220), (pad, pad, rect.w, rect.h), 6, border_radius=22)
            self._cache[key] = (blur(g, 6), pad)
        glow, pad = self._cache[key]
        self.screen.blit(glow, (rect.x-pad, rect.y-pad))
        pygame.draw.rect(self.screen, (6, 6, 22), rect.move(0, 8), border_radius=22)
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=22)
        pygame.draw.rect(self.screen, accent, rect, 2, border_radius=22)
        return rect

    def button(self, rect, label, action, color=ACCENT, size=20, hint=None, active=True):
        rect = pygame.Rect(rect)
        hover = active and rect.collidepoint(self.mouse)
        fill = lighten(color, .18) if hover else (color if active else darken(color, .55))
        pygame.draw.rect(self.screen, darken(color, .55), rect.move(0, 4), border_radius=12)
        pygame.draw.rect(self.screen, fill, rect, border_radius=12)
        pygame.draw.rect(self.screen, lighten(color, .45 if hover else .25), rect, 2, border_radius=12)
        self.text(label, rect.center, size, WHITE if active else MUTED, anchor="center")
        if hint:
            badge = pygame.Rect(rect.x+8, rect.y+8, 22, 20)
            pygame.draw.rect(self.screen, darken(color, .45), badge, border_radius=6)
            self.text(hint, badge.center, 13, lighten(color, .6), bold=True, anchor="center")
        self.buttons.append((rect, action))
        return rect

    def update_cursor(self):
        hand = any(r.collidepoint(self.mouse) for r, _ in self.buttons)
        if hand != self._hand:
            self._hand = hand
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if hand else pygame.SYSTEM_CURSOR_ARROW)
            except (pygame.error, AttributeError):
                pass

    # Personagens e itens
    def draw_pacman_at(self, x, y, angle, radius, mouth):
        self.blit_glow(YELLOW, x, y, int(radius*2.1), 90)
        points = [(x, y)]
        for i in range(31):
            a = angle + mouth*math.pi + (2-2*mouth)*math.pi*i/30
            points.append((x + math.cos(a)*radius, y + math.sin(a)*radius))
        pygame.draw.polygon(self.screen, YELLOW, points)
        eye = angle - math.pi/2 if math.cos(angle) >= -0.01 else angle + math.pi/2
        pygame.draw.circle(self.screen, (30, 20, 10),
                           (int(x + math.cos(eye)*radius*.45 + math.cos(angle)*2),
                            int(y + math.sin(eye)*radius*.45 + math.sin(angle)*2)), max(2, int(radius*.12)))

    def draw_ghost_at(self, x, y, color, dr, dc, r):
        t = pygame.time.get_ticks()
        self.blit_glow(color, x, y, int(r*2.2), 80)
        top = y - 2
        pts = [(x + math.cos(math.pi + math.pi*i/12)*r, top + math.sin(math.pi + math.pi*i/12)*r) for i in range(13)]
        bottom = y + r*.8
        for k in range(13):
            f = k / 12
            pts.append((x + r - 2*r*f, bottom + math.sin(f*math.pi*4 + t/90)*3))
        pygame.draw.polygon(self.screen, color, pts)
        for off in (-.38, .38):
            ex, ey = x + off*r, y - r*.22
            pygame.draw.ellipse(self.screen, WHITE, (ex - r*.2, ey - r*.25, r*.4, r*.5))
            pygame.draw.circle(self.screen, (20, 30, 90), (int(ex + dc*r*.1), int(ey + dr*r*.12)), max(2, int(r*.11)))

    def draw_fruit(self, key, x, y, s=1.0):
        d = self.screen
        if key == "cereja":
            pygame.draw.line(d, (80, 180, 70), (x-6*s, y+2*s), (x+2*s, y-11*s), max(1, int(2*s)))
            pygame.draw.line(d, (80, 180, 70), (x+6*s, y+1*s), (x+2*s, y-11*s), max(1, int(2*s)))
            pygame.draw.ellipse(d, (90, 200, 80), (x+1*s, y-14*s, 9*s, 5*s))
            for cx, cy in ((x-6*s, y+5*s), (x+6*s, y+4*s)):
                pygame.draw.circle(d, (220, 30, 60), (int(cx), int(cy)), int(7*s))
                pygame.draw.circle(d, (255, 150, 170), (int(cx-2*s), int(cy-2*s)), max(1, int(2*s)))
        elif key == "morango":
            body = [(x-10*s, y-4*s), (x+10*s, y-4*s), (x+7*s, y+5*s), (x, y+12*s), (x-7*s, y+5*s)]
            pygame.draw.polygon(d, (235, 45, 70), body)
            pygame.draw.circle(d, (235, 45, 70), (int(x-5*s), int(y-4*s)), int(6*s))
            pygame.draw.circle(d, (235, 45, 70), (int(x+5*s), int(y-4*s)), int(6*s))
            for sx, sy in ((-4, 0), (3, -1), (0, 5), (-2, -5), (5, 4), (-5, 4)):
                pygame.draw.circle(d, (255, 230, 120), (int(x+sx*s), int(y+sy*s)), max(1, int(1.2*s)))
            leaves = [(x-9*s, y-9*s), (x, y-6*s), (x+9*s, y-9*s), (x+3*s, y-12*s), (x, y-15*s), (x-3*s, y-12*s)]
            pygame.draw.polygon(d, (70, 190, 80), leaves)
        elif key == "laranja":
            pygame.draw.circle(d, (255, 150, 30), (int(x), int(y+1*s)), int(11*s))
            pygame.draw.circle(d, (255, 200, 110), (int(x-4*s), int(y-3*s)), max(1, int(3*s)))
            pygame.draw.ellipse(d, (70, 190, 80), (x, y-14*s, 10*s, 6*s))
            self.text("×2", (x, y+2*s), max(10, int(11*s)), (120, 50, 0), bold=True, anchor="center")
        elif key == "uva":
            pygame.draw.line(d, (110, 160, 60), (x, y-8*s), (x+2*s, y-14*s), max(1, int(2*s)))
            for gx, gy in ((-6, -5), (0, -5), (6, -5), (-3, 1), (3, 1), (0, 7)):
                pygame.draw.circle(d, (140, 70, 230), (int(x+gx*s), int(y+gy*s)), int(4.6*s))
                pygame.draw.circle(d, (200, 160, 255), (int(x+gx*s-1.5*s), int(y+gy*s-1.5*s)), max(1, int(1.2*s)))
            self.text("×3", (x, y+18*s), max(10, int(11*s)), (210, 170, 255), bold=True, anchor="center")
        elif key == "melancia":
            c = (int(x), int(y-4*s))
            pygame.draw.circle(d, (40, 150, 60), c, int(14*s), draw_bottom_left=True, draw_bottom_right=True)
            pygame.draw.circle(d, (230, 245, 200), c, int(11*s), draw_bottom_left=True, draw_bottom_right=True)
            pygame.draw.circle(d, (240, 60, 80), c, int(10*s), draw_bottom_left=True, draw_bottom_right=True)
            for sx, sy in ((-5, 3), (0, 6), (5, 3)):
                pygame.draw.ellipse(d, (30, 20, 20), (x+sx*s-1.2*s, y+sy*s-4*s, 2.4*s, 3.6*s))

    def draw_heart(self, x, y, s, color):
        pygame.draw.circle(self.screen, color, (int(x - s*.5), int(y - s*.25)), int(s*.58))
        pygame.draw.circle(self.screen, color, (int(x + s*.5), int(y - s*.25)), int(s*.58))
        pygame.draw.polygon(self.screen, color, [(x - s*1.06, y), (x + s*1.06, y), (x, y + s*1.1)])

    # Mundo do jogo
    def draw_world(self):
        t = pygame.time.get_ticks()
        self.screen.blit(self.background, (0,0))
        self.screen.blit(self.maze_surface, (0,0))
        for (r,c), col in self.dots.items():
            x, y = (c+.5)*TILE, (r+.5)*TILE
            pulse = 1 + .15*math.sin(t/220 + r*1.3 + c)
            self.blit_glow(col, x, y, 16, 90)
            pygame.draw.circle(self.screen, col, (int(x), int(y)), int(7*pulse))
            pygame.draw.circle(self.screen, WHITE, (int(x-2), int(y-2)), 2)
        if self.fruit and not (self.fruit.left < FRUIT_BLINK and (t//140) % 2):
            x, y = self.fruit.pixel()
            y += math.sin(t/260)*3
            self.blit_glow(YELLOW, x, y, int(26 + 4*math.sin(t/180)), 120)
            self.draw_fruit(self.fruit.kind.key, x, y, 1.05)
        for g in self.ghosts:
            gx, gy = g.pixel()
            self.draw_ghost_at(gx, gy, g.color, g.dr, g.dc, TILE*.4)
        if not (self.inv > 0 and (t//120) % 2 == 0):
            x, y = self.player.pixel()
            angle = math.atan2(self.player.dr, self.player.dc)
            mouth = .03 + .2*abs(math.sin(t/110)) if self.state == "play" else .15
            self.draw_pacman_at(x, y, angle, TILE*.42, mouth)
        self.draw_effects()

    def draw_effects(self):
        for p in self.effects.particles:
            k = 1 - p.age/p.life
            pygame.draw.circle(self.screen, p.color, (int(p.x), int(p.y)), max(1, int(3.5*k)))
        for p in self.effects.popups:
            a = int(255 * min(1, 2*(1 - p.age/p.life)))
            self.text(p.text, (p.x+2, p.y+2), p.size, (10, 8, 30), bold=True, anchor="center", alpha=a)
            self.text(p.text, (p.x, p.y), p.size, p.color, bold=True, anchor="center", alpha=a)
        b = self.effects.banner
        if b:
            a = int(255 * min(1, b.age/200, (b.life - b.age)/400))
            band = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
            band.fill((5, 5, 25, int(a*.6)))
            self.screen.blit(band, (0, HEIGHT//2 - 60))
            self.text(b.text, (WIDTH//2, HEIGHT//2 - (14 if b.sub else 0)), 54, b.color,
                      bold=True, anchor="center", alpha=a)
            if b.sub:
                self.text(b.sub, (WIDTH//2, HEIGHT//2 + 34), 20, WHITE, anchor="center", alpha=a)

    def draw_hud(self):
        y0 = HEIGHT
        pygame.draw.rect(self.screen, (14, 12, 46), (0, y0, SCREEN_W, HUD_HEIGHT))
        pygame.draw.line(self.screen, NEON, (0, y0), (SCREEN_W, y0), 2)
        # Corações e modo
        for i in range(HEARTS):
            x = 34 + i*38
            if i < self.hearts: self.blit_glow(RED, x, y0+30, 20, 70)
            self.draw_heart(x, y0+28, 13, RED if i < self.hearts else (60, 50, 90))
        label = f"NÍVEL {self.level_no} de {self.db.level_count()}" if self.mode == "classic" else f"ONDA {self.level_no}"
        self.text(f"{MODE_NAMES[self.mode].upper()} · {label}", (20, y0+56), 15, MUTED)
        self.text(self.player_name, (20, y0+74), 13, darken(MUTED, .25))
        # Pontos e meta
        cx = WIDTH//2 - 20
        self.text("PONTOS", (cx, y0+8), 13, MUTED, anchor="midtop")
        self.text(thousands(self.score.score), (cx, y0+40), 34, YELLOW, bold=True, anchor="center")
        bar = pygame.Rect(cx-130, y0+64, 260, 18)
        pygame.draw.rect(self.screen, (34, 34, 90), bar, border_radius=9)
        if self.mode == "classic":
            ratio = min(1, self.score.level_score / self.level.goal)
            caption = f"Meta {thousands(min(self.score.level_score, self.level.goal))} / {thousands(self.level.goal)}"
            fill_color = GREEN
        else:
            ratio = self.eaten / max(1, self.eaten + len(self.dots))
            caption = f"Docinhos {self.eaten} / {self.eaten + len(self.dots)}"
            fill_color = PURPLE
        if ratio > 0:
            pygame.draw.rect(self.screen, fill_color, (bar.x, bar.y, max(18, int(bar.w*ratio)), bar.h), border_radius=9)
        self.text(caption, bar.center, 13, WHITE, bold=True, anchor="center")
        # Multiplicador e sequência
        mx, my = SCREEN_W - 52, y0 + 46
        mult = self.score.multiplier
        if mult > 1:
            color = ORANGE if mult == 2 else PURPLE
            self.blit_glow(color, mx, my, 44, 120)
            pygame.draw.circle(self.screen, darken(color, .55), (mx, my), 30)
            frac = self.score.mult_left / max(1, self.score.mult_total)
            pygame.draw.arc(self.screen, color, (mx-30, my-30, 60, 60), math.pi/2, math.pi/2 + 2*math.pi*frac, 5)
            self.text(f"×{mult}", (mx, my), 24, WHITE, bold=True, anchor="center")
        else:
            pygame.draw.circle(self.screen, (30, 30, 80), (mx, my), 30)
            pygame.draw.circle(self.screen, (60, 60, 120), (mx, my), 30, 2)
            self.text("×1", (mx, my), 22, MUTED, bold=True, anchor="center")
        rx = SCREEN_W - 98
        self.text("SEQUÊNCIA", (rx, y0+12), 12, MUTED, anchor="topright")
        streak = self.score.streak
        self.text(f"{streak} acerto{'s' if streak != 1 else ''}", (rx, y0+28), 18,
                  GREEN if streak >= 2 else WHITE, bold=True, anchor="topright")
        self.text("Setas/WASD · ESC pausa", (rx, y0+66), 12, darken(MUTED, .2), anchor="topright")

    # Telas
    def draw(self):
        self.buttons = []
        self.mouse = pygame.mouse.get_pos()
        if self.state in ("menu", "ranking"):
            self.screen.blit(self.background, (0,0))
            self.screen.blit(self.maze_surface, (0,0))
            self.dim(220)
            self.draw_menu() if self.state == "menu" else self.draw_ranking()
        else:
            self.draw_world()
            self.draw_hud()
            screen = {"pause": self.draw_pause, "quiz": self.draw_quiz, "feedback": self.draw_feedback,
                      "level_up": self.draw_level_up, "over": self.draw_game_over,
                      "victory": self.draw_game_over}.get(self.state)
            if screen: screen()
        self.update_cursor()

    def draw_chase(self, y):
        t = pygame.time.get_ticks()
        x = (t*.16) % (SCREEN_W + 260) - 130
        for dx in range(40, SCREEN_W, 44):
            if dx > x + 8:
                pygame.draw.circle(self.screen, CANDY_COLORS[(dx//44) % len(CANDY_COLORS)], (dx, y), 5)
        self.draw_pacman_at(x, y, 0, 15, .03 + .2*abs(math.sin(t/110)))
        self.draw_ghost_at(x - 62, y, GHOST_STARTS[0][2], 0, 1, 14)
        self.draw_ghost_at(x - 104, y, GHOST_STARTS[1][2], 0, 1, 14)

    def player_stats(self):
        key = ("stats", self.player_name.strip().lower(), self.last_score_id)
        if self._cache.get("stats_key") != key:
            self._cache["stats_key"] = key
            self._cache["stats"] = self.db.player_stats(self.player_name) if self.player_name.strip() else None
        return self._cache["stats"]

    def draw_menu(self):
        t = pygame.time.get_ticks()
        self.glow_text("PAC-LÓGICA", (CX, 68), 64, YELLOW)
        self.text("Lógica proposicional no labirinto", (CX, 116), 18, MUTED, anchor="center")
        self.draw_chase(156)
        # Nome do jogador
        self.text("NOME DO JOGADOR", (CX, 188), 13, MUTED, anchor="center")
        box = pygame.Rect(CX-170, 202, 340, 46)
        pygame.draw.rect(self.screen, (16, 16, 54), box, border_radius=12)
        pygame.draw.rect(self.screen, NEON, box, 2, border_radius=12)
        if self.player_name:
            r = self.text(self.player_name, box.center, 22, WHITE, anchor="center")
            caret_x = r.right + 3
        else:
            self.text("Digite seu nome", box.center, 20, darken(MUTED, .3), anchor="center")
            caret_x = box.centerx + self.text_width("Digite seu nome", 20)//2 + 3
        if (t//500) % 2 == 0:
            pygame.draw.line(self.screen, YELLOW, (caret_x, box.y+11), (caret_x, box.bottom-11), 2)
        stats = self.player_stats()
        if stats and stats["games"]:
            info = (f"Melhor nível: {stats['best_level'] or '-'} · Recorde tradicional: {thousands(stats['best_classic'])}"
                    f" · Recorde arcade: {thousands(stats['best_arcade'])}")
        else:
            info = "Digite seu nome e escolha um modo de jogo"
        self.text(info, (CX, 266), 14, MUTED, anchor="center")
        # Modos de jogo
        levels = self.db.level_count()
        cards = [
            ("classic", "Tradicional", f"Atinja a meta de pontos para subir de nível. São {levels} níveis, "
                                       "das regras dos conectivos até as tabelas-verdade.", GREEN),
            ("arcade", "Arcade", "Sem fases: some o máximo de pontos até perder todos os corações "
                                 "e entre no ranking de jogadores.", ORANGE),
        ]
        for i, (action, title, desc, color) in enumerate(cards):
            rect = pygame.Rect(CX - 362 + i*374, 292, 350, 172)
            hover = rect.collidepoint(self.mouse)
            if hover: self.blit_glow(color, rect.centerx, rect.centery, 190, 60)
            pygame.draw.rect(self.screen, (6, 6, 22), rect.move(0, 6), border_radius=18)
            pygame.draw.rect(self.screen, lighten(PANEL, .08) if hover else PANEL, rect, border_radius=18)
            pygame.draw.rect(self.screen, color if hover else darken(color, .35), rect, 3 if hover else 2, border_radius=18)
            if action == "classic":
                self.draw_pacman_at(rect.x+34, rect.y+34, 0, 15, .2)
            else:
                self.draw_ghost_at(rect.x+34, rect.y+34, GHOST_STARTS[1][2], 0, 1, 15)
            self.text(title, (rect.x+62, rect.y+34), 28, WHITE, bold=True, anchor="midleft")
            self.paragraph(desc, (rect.x+20, rect.y+62), 15, rect.w-40, MUTED, anchor="topleft", spacing=3)
            pill = pygame.Rect(rect.right-108, rect.bottom-44, 92, 32)
            pygame.draw.rect(self.screen, color if hover else darken(color, .3), pill, border_radius=16)
            self.text("JOGAR", pill.center, 15, (10, 20, 30) if hover else WHITE, bold=True, anchor="center")
            self.buttons.append((rect, action))
        # Legenda das frutas
        self.text("FRUTAS ESPECIAIS", (CX, 486), 13, MUTED, anchor="center")
        step = 140
        for i, f in enumerate(FRUITS):
            x = CX + (i - (len(FRUITS)-1)/2) * step
            self.draw_fruit(f.key, x, 524, 1.05)
            self.text(f.name, (x, 556), 14, WHITE, anchor="center")
            self.text(f.label(), (x, 574), 14, f.color, bold=True, anchor="center")
        self.button((CX-170, 612, 160, 46), "Ranking", "ranking", ACCENT)
        self.button((CX+10, 612, 160, 46), "Sair", "quit", BAD_BTN)
        self.text("Respostas: teclas 1 a 4 · Pausa: ESC", (CX, 684), 12, darken(MUTED, .2), anchor="center")

    def draw_ranking(self):
        self.glow_text("RANKING", (CX, 56), 52, YELLOW)
        for i, mode in enumerate(("arcade", "classic")):
            active = self.ranking_mode == mode
            self.button((CX - 190 + i*200, 98, 180, 42), MODE_NAMES[mode], ("tab", mode),
                        ACCENT if active else (40, 44, 100), 18)
        table = self.panel((60, 160, SCREEN_W-120, 430))
        level_label = "NÍVEL" if self.ranking_mode == "classic" else "ONDA"
        cols = {"#": table.x+40, "JOGADOR": table.x+80, "PONTOS": table.x+420,
                level_label: table.x+500, "DATA": table.right-30}
        hy = table.y + 28
        self.text("#", (cols["#"], hy), 13, MUTED, anchor="center")
        self.text("JOGADOR", (cols["JOGADOR"], hy), 13, MUTED, anchor="midleft")
        self.text("PONTOS", (cols["PONTOS"], hy), 13, MUTED, anchor="midright")
        self.text(level_label, (cols[level_label], hy), 13, MUTED, anchor="center")
        self.text("DATA", (cols["DATA"], hy), 13, MUTED, anchor="midright")
        pygame.draw.line(self.screen, (60, 66, 150), (table.x+20, hy+18), (table.right-20, hy+18), 1)
        rows = self.db.top_scores(self.ranking_mode, 10)
        if not rows:
            self.text("Nenhuma partida registrada ainda. Seja o primeiro!", table.center, 18, MUTED, anchor="center")
        medals = [(255, 205, 60), (200, 210, 230), (215, 140, 80)]
        for i, row in enumerate(rows):
            y = hy + 52 + i*36
            if row["id"] == self.last_score_id:
                pygame.draw.rect(self.screen, (50, 60, 160), (table.x+14, y-16, table.w-28, 32), border_radius=8)
            if i < 3:
                pygame.draw.circle(self.screen, medals[i], (cols["#"], y), 13)
                self.text(i+1, (cols["#"], y), 15, (30, 20, 10), bold=True, anchor="center")
            else:
                self.text(i+1, (cols["#"], y), 16, MUTED, anchor="center")
            self.text(row["player"], (cols["JOGADOR"], y), 18, WHITE, anchor="midleft")
            self.text(thousands(row["score"]), (cols["PONTOS"], y), 18, YELLOW, bold=True, anchor="midright")
            self.text(row["level"], (cols[level_label], y), 17, WHITE, anchor="center")
            try:
                date = datetime.fromisoformat(row["created_at"]).strftime("%d/%m/%y")
            except ValueError:
                date = "-"
            self.text(date, (cols["DATA"], y), 15, MUTED, anchor="midright")
        self.button((CX-120, 620, 240, 48), "Voltar ao menu", "menu", ACCENT)

    def quiz_panel(self):
        self.dim(175)
        return self.panel((50, 34, SCREEN_W-100, SCREEN_H-68))

    LINE_STYLES = {"big": (44, YELLOW), "text": (22, WHITE), "accent": (22, YELLOW), "muted": (17, MUTED)}

    def question_box(self, lines, top, width=620):
        rows = []
        for text, style in lines:
            size, color = self.LINE_STYLES[style]
            wrapped = self.wrap(text, size, width - 48) if text else [""]
            rows += [(line, size, color) for line in wrapped]
        heights = [size + 10 if line else 8 for line, size, _ in rows]
        box = pygame.Rect(CX - width//2, top, width, max(84, sum(heights) + 36))
        pygame.draw.rect(self.screen, (10, 10, 40), box, border_radius=16)
        pygame.draw.rect(self.screen, NEON, box, 2, border_radius=16)
        y = box.centery - sum(heights)/2
        for (line, size, color), h in zip(rows, heights):
            if line: self.text(line, (CX, y + h/2), size, color, anchor="center")
            y += h
        return box.bottom

    def draw_options(self, options, top):
        n = len(options)
        widest = max(self.text_width(o, 20) for o in options)
        if widest > 250 or (n == 3 and widest > 180):
            for i, label in enumerate(options):
                self.button((CX - 310, top + i*64, 620, 54), label, ("answer", i), ACCENT, 20, str(i+1))
        elif n == 4:
            for i, label in enumerate(options):
                self.button((CX - 310 + (i % 2)*320, top + (i // 2)*82, 300, 68), label, ("answer", i), ACCENT, 24, str(i+1))
        else:
            w = (640 - 16*(n-1)) // n
            for i, label in enumerate(options):
                self.button((CX - 320 + i*(w+16), top, w, 68), label, ("answer", i), ACCENT, 22, str(i+1))

    def draw_timer(self, y):
        left = max(0, self.quiz_left)
        secs = math.ceil(left / 1000)
        color = GREEN if secs > 8 else ORANGE if secs > 4 else RED
        bar = pygame.Rect(CX - 220, y, 440, 14)
        pygame.draw.rect(self.screen, (34, 34, 90), bar, border_radius=7)
        if left > 0:
            pygame.draw.rect(self.screen, color, (bar.x, bar.y, max(14, int(bar.w*left/QUIZ_TIME)), bar.h), border_radius=7)
        self.text(f"{secs}s", (bar.right + 14, bar.centery), 18, color, bold=True, anchor="midleft")

    def draw_quiz(self):
        q = self.question
        self.quiz_panel()
        if self.quiz_mode == "eat":
            self.glow_text("QUESTÃO DE LÓGICA", (CX, 74), 32, YELLOW)
            stake = f"Acerte e ganhe {plural(self.score.preview_correct(), 'ponto')} · Errar custa 1 coração"
            if self.score.multiplier > 1: stake += f" · ×{self.score.multiplier} ativo"
        else:
            self.glow_text("CHANCE DE REVIVER", (CX, 74), 32, RED)
            stake = f"Acerte para voltar com {REVIVE_HEARTS} corações. Só há uma chance!"
        self.text(stake, (CX, 110), 16, MUTED, anchor="center")
        self.draw_timer(132)
        self.text(q["prompt"], (CX, 176), 21, WHITE, anchor="center")
        bottom = self.question_box(q["lines"], 198)
        self.draw_options(q["options"], bottom + 24)
        self.text("Clique na resposta ou use as teclas 1 a 4", (CX, SCREEN_H-70), 14, darken(MUTED, .15), anchor="center")

    def truth_table(self, headers, rows, top, n_inputs):
        widths = [max(58, self.text_width(h, 20) + 32) for h in headers]
        total, rh = sum(widths), 34
        x0 = CX - total//2
        pygame.draw.rect(self.screen, (40, 46, 120), (x0, top, total, rh),
                         border_top_left_radius=10, border_top_right_radius=10)
        x = x0
        for h, w in zip(headers, widths):
            self.text(h, (x + w/2, top + rh/2), 20, WHITE, anchor="center"); x += w
        for i, row in enumerate(rows):
            y = top + rh*(i+1)
            pygame.draw.rect(self.screen, (24, 26, 74) if i % 2 == 0 else (30, 32, 86), (x0, y, total, rh))
            x = x0
            for v, w in zip(row, widths):
                self.text("V" if v else "F", (x + w/2, y + rh/2), 20, GREEN if v else RED, bold=True, anchor="center")
                x += w
        bottom = top + rh*(len(rows)+1)
        split = x0 + sum(widths[:n_inputs])
        pygame.draw.line(self.screen, NEON, (split, top), (split, bottom-1), 2)
        pygame.draw.rect(self.screen, NEON, (x0, top, total, bottom-top), 2, border_radius=10)
        return bottom

    def draw_feedback(self):
        q, ok = self.question, self.feedback
        self.quiz_panel()
        title = "CORRETO!" if ok else "TEMPO ESGOTADO!" if self.timed_out else "ERROU!"
        self.glow_text(title, (CX, 84), 44, GREEN if ok else RED)
        if self.quiz_mode == "eat":
            sub = (f"+{plural(self.last_points, 'ponto')}", YELLOW) if ok else ("Você perdeu 1 coração.", RED)
        else:
            sub = (f"Você voltou com {REVIVE_HEARTS} corações!", GREEN) if ok else ("Não foi dessa vez...", RED)
        self.text(sub[0], (CX, 132), 24, sub[1], bold=True, anchor="center")
        self.text(f"Resposta correta: {q['options'][q['answer']]}", (CX, 178), 20, WHITE, anchor="center")
        y = self.paragraph(q["explanation"], (CX, 204), 17, 620, MUTED, spacing=4)
        if q.get("table"):
            headers, rows, inputs = q["table"]
            self.truth_table(headers, rows, y + 16, inputs)
        self.button((CX-130, SCREEN_H-130, 260, 56), "Continuar (Enter)", "continue",
                    GOOD_BTN if ok else ACCENT, 21)

    def draw_pause(self):
        self.dim(170)
        rect = self.panel((CX-200, 190, 400, 300))
        self.glow_text("PAUSADO", (CX, rect.y+56), 40, YELLOW)
        self.button((CX-130, rect.y+110, 260, 52), "Continuar", "resume", GOOD_BTN, 20)
        self.button((CX-130, rect.y+178, 260, 52), "Menu principal", "menu", ACCENT, 20)
        self.text("Voltar ao menu encerra a partida sem salvar.", (CX, rect.bottom-30), 13, MUTED, anchor="center")

    def draw_level_scale(self, y, done):
        """Escala de níveis: concluídos em verde, o próximo em amarelo."""
        total = self.db.level_count()
        step = min(64, 520 // max(1, total - 1))
        x0 = CX - step * (total - 1) / 2
        for i in range(total - 1):
            color = GREEN if i < done else (60, 60, 120)
            pygame.draw.line(self.screen, color, (x0 + i*step, y), (x0 + (i+1)*step, y), 4)
        for i in range(total):
            x, n = x0 + i*step, i + 1
            if n <= done:
                pygame.draw.circle(self.screen, GREEN, (int(x), y), 16)
                self.text(n, (x, y), 16, (10, 40, 20), bold=True, anchor="center")
            elif n == done + 1:
                self.blit_glow(YELLOW, x, y, 34, 140)
                pygame.draw.circle(self.screen, YELLOW, (int(x), y), 18)
                self.text(n, (x, y), 17, (40, 30, 0), bold=True, anchor="center")
            else:
                pygame.draw.circle(self.screen, (30, 30, 80), (int(x), y), 16)
                pygame.draw.circle(self.screen, (70, 70, 140), (int(x), y), 16, 2)
                self.text(n, (x, y), 15, MUTED, anchor="center")

    def draw_level_up(self):
        self.dim(170)
        rect = self.panel((CX-310, 70, 620, 540), GREEN)
        self.glow_text(f"NÍVEL {self.level_no} CONCLUÍDO!", (CX, rect.y+56), 38, GREEN)
        self.text("ESCALA DE NÍVEIS", (CX, rect.y+104), 13, MUTED, anchor="center")
        self.draw_level_scale(rect.y + 140, self.level_no)
        nxt = self.db.level(self.level_no + 1)
        new = [t for t in nxt.topic_list if t not in self.level.topic_list]
        lines = [
            (f"Pontuação total: {thousands(self.score.score)}", YELLOW, 26, True),
            (f"Próximo nível: meta de {plural(nxt.goal, 'ponto')}", WHITE, 20, False),
            ("Questões: " + " · ".join(TOPIC_NAMES.get(t, t) for t in nxt.topic_list), WHITE, 17, False),
            (("Novo tipo de questão: " + " · ".join(TOPIC_NAMES.get(t, t) for t in new)) if new else "",
             YELLOW, 17, True),
            (f"{nxt.ghosts} fantasmas · {nxt.dots} docinhos · fantasmas mais rápidos", MUTED, 16, False),
            ("Corações restaurados!", RED, 18, False),
        ]
        y = rect.y + 196
        for s, color, size, bold in lines:
            if s: self.text(s, (CX, y), size, color, bold=bold, anchor="center")
            y += size + 20
        self.button((CX-140, rect.bottom-84, 280, 56), "Próximo nível", "next_level", GOOD_BTN, 22)

    def draw_game_over(self):
        victory = self.state == "victory"
        self.dim(180)
        color = GREEN if victory else RED
        rect = self.panel((CX-310, 90, 620, 500), color)
        self.glow_text("VOCÊ VENCEU!" if victory else "FIM DE JOGO", (CX, rect.y+60), 48, color)
        sub = "Todos os níveis do modo tradicional concluídos!" if victory else self.player_name
        self.text(sub, (CX, rect.y+110), 20, WHITE, anchor="center")
        self.text("PONTUAÇÃO FINAL", (CX, rect.y+158), 14, MUTED, anchor="center")
        self.glow_text(thousands(self.score.score), (CX, rect.y+202), 56, YELLOW)
        reached = f"Nível alcançado: {self.level_no}" if self.mode == "classic" else f"Onda alcançada: {self.level_no}"
        self.text(reached, (CX, rect.y+254), 20, WHITE, anchor="center")
        if self.last_rank:
            if self.last_rank == 1:
                self.text("NOVO RECORDE!", (CX, rect.y+300), 26, YELLOW, bold=True, anchor="center")
            self.text(f"{self.last_rank}º lugar no ranking {MODE_NAMES[self.mode]}",
                      (CX, rect.y+336), 19, MUTED, anchor="center")
        y = rect.bottom - 82
        self.button((CX-285, y, 190, 54), "Jogar novamente", "again", GOOD_BTN, 19)
        self.button((CX-85, y, 170, 54), "Ranking", "ranking", ACCENT, 19)
        self.button((CX+95, y, 190, 54), "Menu", "menu", (60, 64, 130), 19)
