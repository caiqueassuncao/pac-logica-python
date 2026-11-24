import math
import random
from datetime import datetime
import pygame
from .config import *
from .questions import TOPIC_NAMES
from .scoring import FRUITS, plural
from .maze import current_map

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

OVERLAYS = ("pause", "quiz", "feedback", "level_up", "over", "victory")
MEDALS = [(255, 205, 80), (205, 214, 232), (218, 150, 96)]

class RendererMixin:
    # Recursos pré-renderizados (refeitos ao trocar a proporção)
    def prerender(self):
        L = self.layout
        self._cache = {}
        self._hand = None
        self._backdrop = None
        self.mouse = (0, 0)
        self.k = L.tile / TILE
        self.cx = L.w // 2
        self.background = self.make_background()
        self.maze_surface = self.make_maze()
        menu = self.background.copy()
        shade = pygame.Surface(L.size, pygame.SRCALPHA)
        shade.fill((8, 8, 26, 90))
        menu.blit(shade, (0, 0))
        self.menu_background = menu

    def make_background(self):
        w, h = self.layout.size
        surf = pygame.Surface((w, h))
        for y in range(h):
            pygame.draw.line(surf, mix(BG_TOP, BG_BOTTOM, y/h), (0, y), (w, y))
        # Manchas de cor suaves (aurora) e vinheta nas bordas.
        blobs = pygame.Surface((w//8, h//8), pygame.SRCALPHA)
        for fx, fy, r, color, a in [(.12, .18, .42, (96, 70, 210), 70), (.88, .82, .46, (40, 96, 200), 60),
                                    (.62, .06, .3, (170, 70, 170), 40), (.3, .95, .3, (60, 140, 170), 35)]:
            pygame.draw.circle(blobs, (*color, a), (int(fx*w/8), int(fy*h/8)), int(r*h/8))
        surf.blit(pygame.transform.smoothscale(blur(blobs, 4), (w, h)), (0, 0))
        vignette = pygame.Surface((32, 18), pygame.SRCALPHA)
        for vy in range(18):
            for vx in range(32):
                d = math.hypot((vx - 15.5)/16, (vy - 8.5)/9)
                vignette.set_at((vx, vy), (0, 0, 10, int(150 * max(0, d - .55) / .9)))
        surf.blit(pygame.transform.smoothscale(vignette, (w, h)), (0, 0))
        rng = random.Random(7)
        for _ in range(w // 9):
            c = rng.randint(60, 120)
            surf.set_at((rng.randrange(w), rng.randrange(h)), (c, c, min(255, c + 40)))
        return surf

    def make_maze(self):
        T, k = self.layout.tile, self.k
        grid = current_map().grid
        size = (COLS*T, ROWS*T)
        surf = pygame.Surface(size, pygame.SRCALPHA)
        lines = pygame.Surface(size, pygame.SRCALPHA)
        lines.fill((*NEON, 0))
        inner = pygame.Rect(T, T, (COLS-2)*T, (ROWS-2)*T).inflate(int(8*k), int(8*k))
        radius = int(16*k)
        pygame.draw.rect(surf, (*WALL_FILL, 255), surf.get_rect(), border_radius=int(24*k))
        pygame.draw.rect(surf, (10, 10, 30, 120), inner, border_radius=radius)
        pygame.draw.rect(lines, (*NEON, 230), inner, 2, border_radius=radius)
        pygame.draw.rect(lines, (*NEON_SOFT, 90), inner.inflate(int(10*k), int(10*k)), 1, border_radius=radius+4)
        pygame.draw.rect(lines, (*NEON_SOFT, 150), surf.get_rect().inflate(-int(12*k), -int(12*k)), 2,
                         border_radius=int(20*k))
        # Paredes internas como blocos arredondados por trecho horizontal.
        for r in range(1, ROWS-1):
            c = 1
            while c < COLS-1:
                if grid[r][c] != "#":
                    c += 1
                    continue
                start = c
                while c < COLS-1 and grid[r][c] == "#": c += 1
                rect = pygame.Rect(start*T + .14*T, r*T + .17*T, (c-start)*T - .28*T, T - .34*T)
                pygame.draw.rect(surf, (*lighten(WALL_FILL, .04), 255), rect, border_radius=int(.3*T))
                pygame.draw.rect(lines, (*NEON, 230), rect, 2, border_radius=int(.3*T))
        surf.blit(blur(lines, 6), (0, 0))
        surf.blit(lines, (0, 0))
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
        radius = max(2, int(radius))
        self.screen.blit(self.glow(color, radius, strength), (x-radius, y-radius))

    def rounded_gradient(self, size, top, bottom, radius):
        key = ("grad", size, top, bottom, radius)
        if key not in self._cache:
            w, h = size
            s = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 255, 255, 255), s.get_rect(), border_radius=radius)
            grad = pygame.Surface(size)
            for y in range(h):
                pygame.draw.line(grad, mix(top, bottom, y / max(1, h-1)), (0, y), (w, y))
            s.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self._cache[key] = s
        return self._cache[key]

    def to_screen(self, x, y):
        """Converte coordenadas lógicas do jogo (TILE) para a tela atual."""
        w = self.layout.world
        return w.x + x*self.k, w.y + y*self.k

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
            glow = blur(g, 5)
            glow.set_alpha(190)
            self._cache[key] = (surf, glow, pad)
        surf, glow, pad = self._cache[key]
        rect = surf.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
        self.screen.blit(glow, rect.move(-pad, -pad))
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
    def panel(self, rect, accent=PANEL_EDGE, radius=22, glow=True):
        rect = pygame.Rect(rect)
        if glow:
            key = ("panel", rect.size, accent, radius)
            if key not in self._cache:
                pad = 26
                g = pygame.Surface((rect.w+2*pad, rect.h+2*pad), pygame.SRCALPHA)
                g.fill((*accent, 0))
                pygame.draw.rect(g, (*accent, 150), (pad, pad, rect.w, rect.h), 5, border_radius=radius)
                self._cache[key] = (blur(g, 7), pad)
            halo, pad = self._cache[key]
            self.screen.blit(halo, (rect.x-pad, rect.y-pad))
        pygame.draw.rect(self.screen, (6, 6, 20), rect.move(0, 8), border_radius=radius)
        self.screen.blit(self.rounded_gradient(rect.size, lighten(PANEL, .06), darken(PANEL, .18), radius), rect)
        pygame.draw.rect(self.screen, mix(PANEL, accent, .75), rect, 2, border_radius=radius)
        pygame.draw.line(self.screen, lighten(PANEL, .16), (rect.x+radius, rect.y+3), (rect.right-radius, rect.y+3))
        return rect

    def card(self, rect, title=None):
        rect = pygame.Rect(rect)
        self.screen.blit(self.rounded_gradient(rect.size, lighten(PANEL, .04), darken(PANEL, .12), 16), rect)
        pygame.draw.rect(self.screen, mix(PANEL, PANEL_EDGE, .35), rect, 1, border_radius=16)
        if title:
            self.text(title, (rect.x + 16, rect.y + 12), 12, MUTED, bold=True)
        return rect

    def button(self, rect, label, action, color=ACCENT, size=20, hint=None, active=True):
        rect = pygame.Rect(rect)
        hover = active and rect.collidepoint(self.mouse)
        body = rect.move(0, -2) if hover else rect
        base = color if active else darken(color, .5)
        pygame.draw.rect(self.screen, darken(base, .6), rect.move(0, 4), border_radius=14)
        self.screen.blit(self.rounded_gradient(body.size, lighten(base, .26 if hover else .14),
                                               darken(base, .1), 14), body)
        pygame.draw.rect(self.screen, lighten(base, .38 if hover else .2), body, 1, border_radius=14)
        self.text(label, (body.centerx, body.centery + 1), size, (8, 8, 24), anchor="center", alpha=90)
        self.text(label, body.center, size, WHITE if active else MUTED, anchor="center")
        if hint:
            badge = pygame.Rect(body.x+9, body.y+9, 22, 20)
            pygame.draw.rect(self.screen, darken(base, .35), badge, border_radius=6)
            self.text(hint, badge.center, 13, lighten(base, .65), bold=True, anchor="center")
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
        self.blit_glow(YELLOW, x, y, radius*2.1, 80)
        points = [(x, y)]
        for i in range(31):
            a = angle + mouth*math.pi + (2-2*mouth)*math.pi*i/30
            points.append((x + math.cos(a)*radius, y + math.sin(a)*radius))
        pygame.draw.polygon(self.screen, YELLOW, points)
        eye = angle - math.pi/2 if math.cos(angle) >= -0.01 else angle + math.pi/2
        pygame.draw.circle(self.screen, (40, 28, 12),
                           (int(x + math.cos(eye)*radius*.45 + math.cos(angle)*2),
                            int(y + math.sin(eye)*radius*.45 + math.sin(angle)*2)), max(2, int(radius*.12)))

    def draw_ghost_at(self, x, y, color, dr, dc, r):
        t = pygame.time.get_ticks()
        self.blit_glow(color, x, y, r*2.2, 70)
        top = y - 2
        pts = [(x + math.cos(math.pi + math.pi*i/12)*r, top + math.sin(math.pi + math.pi*i/12)*r) for i in range(13)]
        bottom = y + r*.8
        for k in range(13):
            f = k / 12
            pts.append((x + r - 2*r*f, bottom + math.sin(f*math.pi*4 + t/90)*r*.18))
        pygame.draw.polygon(self.screen, color, pts)
        pygame.draw.circle(self.screen, lighten(color, .35), (int(x - r*.45), int(top - r*.45)), max(1, int(r*.14)))
        for off in (-.38, .38):
            ex, ey = x + off*r, y - r*.22
            pygame.draw.ellipse(self.screen, WHITE, (ex - r*.2, ey - r*.25, r*.4, r*.5))
            pygame.draw.circle(self.screen, (24, 34, 96), (int(ex + dc*r*.1), int(ey + dr*r*.12)), max(2, int(r*.11)))

    def draw_fruit(self, key, x, y, s=1.0):
        d = self.screen
        if key == "cereja":
            pygame.draw.line(d, (80, 180, 70), (x-6*s, y+2*s), (x+2*s, y-11*s), max(1, int(2*s)))
            pygame.draw.line(d, (80, 180, 70), (x+6*s, y+1*s), (x+2*s, y-11*s), max(1, int(2*s)))
            pygame.draw.ellipse(d, (90, 200, 80), (x+1*s, y-14*s, 9*s, 5*s))
            for cx, cy in ((x-6*s, y+5*s), (x+6*s, y+4*s)):
                pygame.draw.circle(d, (220, 40, 70), (int(cx), int(cy)), int(7*s))
                pygame.draw.circle(d, (255, 160, 178), (int(cx-2*s), int(cy-2*s)), max(1, int(2*s)))
        elif key == "morango":
            body = [(x-10*s, y-4*s), (x+10*s, y-4*s), (x+7*s, y+5*s), (x, y+12*s), (x-7*s, y+5*s)]
            pygame.draw.polygon(d, (232, 56, 80), body)
            pygame.draw.circle(d, (232, 56, 80), (int(x-5*s), int(y-4*s)), int(6*s))
            pygame.draw.circle(d, (232, 56, 80), (int(x+5*s), int(y-4*s)), int(6*s))
            for sx, sy in ((-4, 0), (3, -1), (0, 5), (-2, -5), (5, 4), (-5, 4)):
                pygame.draw.circle(d, (255, 230, 130), (int(x+sx*s), int(y+sy*s)), max(1, int(1.2*s)))
            leaves = [(x-9*s, y-9*s), (x, y-6*s), (x+9*s, y-9*s), (x+3*s, y-12*s), (x, y-15*s), (x-3*s, y-12*s)]
            pygame.draw.polygon(d, (80, 190, 90), leaves)
        elif key == "laranja":
            pygame.draw.circle(d, (255, 156, 44), (int(x), int(y+1*s)), int(11*s))
            pygame.draw.circle(d, (255, 204, 120), (int(x-4*s), int(y-3*s)), max(1, int(3*s)))
            pygame.draw.ellipse(d, (80, 190, 90), (x, y-14*s, 10*s, 6*s))
            self.text("×2", (x, y+2*s), max(10, int(11*s)), (120, 50, 0), bold=True, anchor="center")
        elif key == "uva":
            pygame.draw.line(d, (110, 160, 60), (x, y-8*s), (x+2*s, y-14*s), max(1, int(2*s)))
            for gx, gy in ((-6, -5), (0, -5), (6, -5), (-3, 1), (3, 1), (0, 7)):
                pygame.draw.circle(d, (146, 84, 230), (int(x+gx*s), int(y+gy*s)), int(4.6*s))
                pygame.draw.circle(d, (206, 170, 255), (int(x+gx*s-1.5*s), int(y+gy*s-1.5*s)), max(1, int(1.2*s)))
            self.text("×3", (x, y+18*s), max(10, int(11*s)), (214, 180, 255), bold=True, anchor="center")
        elif key == "melancia":
            c = (int(x), int(y-4*s))
            pygame.draw.circle(d, (44, 150, 70), c, int(14*s), draw_bottom_left=True, draw_bottom_right=True)
            pygame.draw.circle(d, (230, 245, 205), c, int(11*s), draw_bottom_left=True, draw_bottom_right=True)
            pygame.draw.circle(d, (238, 72, 92), c, int(10*s), draw_bottom_left=True, draw_bottom_right=True)
            for sx, sy in ((-5, 3), (0, 6), (5, 3)):
                pygame.draw.ellipse(d, (30, 20, 20), (x+sx*s-1.2*s, y+sy*s-4*s, 2.4*s, 3.6*s))

    def draw_heart(self, x, y, s, color):
        pygame.draw.circle(self.screen, color, (int(x - s*.5), int(y - s*.25)), int(s*.58))
        pygame.draw.circle(self.screen, color, (int(x + s*.5), int(y - s*.25)), int(s*.58))
        pygame.draw.polygon(self.screen, color, [(x - s*1.06, y), (x + s*1.06, y), (x, y + s*1.1)])

    # Mundo do jogo
    def draw_world(self):
        L, t = self.layout, pygame.time.get_ticks()
        T, ox, oy = L.tile, L.world.x, L.world.y
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.maze_surface, L.world.topleft)
        for (r, c), col in self.dots.items():
            x, y = ox + (c+.5)*T, oy + (r+.5)*T
            pulse = 1 + .12*math.sin(t/240 + r*1.3 + c)
            self.blit_glow(col, x, y, .42*T, 70)
            pygame.draw.circle(self.screen, col, (int(x), int(y)), int(.2*T*pulse))
            pygame.draw.circle(self.screen, WHITE, (int(x - .05*T), int(y - .05*T)), max(1, int(.05*T)))
        if self.fruit and not (self.fruit.left < FRUIT_BLINK and (t//140) % 2):
            x, y = self.to_screen(*self.fruit.pixel())
            y += math.sin(t/260)*3*self.k
            self.blit_glow(YELLOW, x, y, (26 + 4*math.sin(t/180))*self.k, 100)
            self.draw_fruit(self.fruit.kind.key, x, y, 1.05*self.k)
        for g in self.ghosts:
            gx, gy = self.to_screen(*g.pixel())
            self.draw_ghost_at(gx, gy, g.color, g.dr, g.dc, T*.4)
        if not (self.inv > 0 and (t//120) % 2 == 0):
            x, y = self.to_screen(*self.player.pixel())
            angle = math.atan2(self.player.dr, self.player.dc)
            mouth = .03 + .2*abs(math.sin(t/110)) if self.state == "play" else .15
            self.draw_pacman_at(x, y, angle, T*.42, mouth)
        self.draw_effects()

    def draw_effects(self):
        k, world = self.k, self.layout.world
        for p in self.effects.particles:
            x, y = self.to_screen(p.x, p.y)
            pygame.draw.circle(self.screen, p.color, (int(x), int(y)), max(1, int(3.5*k*(1 - p.age/p.life))))
        for p in self.effects.popups:
            x, y = self.to_screen(p.x, p.y)
            a = int(255 * min(1, 2*(1 - p.age/p.life)))
            size = int(p.size*k)
            self.text(p.text, (x+2, y+2), size, (10, 8, 30), bold=True, anchor="center", alpha=a)
            self.text(p.text, (x, y), size, p.color, bold=True, anchor="center", alpha=a)
        b = self.effects.banner
        if b:
            a = int(255 * min(1, b.age/200, (b.life - b.age)/400))
            band = pygame.Surface((world.w, 124), pygame.SRCALPHA)
            band.fill((6, 6, 26, int(a*.6)))
            self.screen.blit(band, (world.x, world.centery - 62))
            self.text(b.text, (world.centerx, world.centery - (14 if b.sub else 0)), 56, b.color,
                      bold=True, anchor="center", alpha=a)
            if b.sub:
                self.text(b.sub, (world.centerx, world.centery + 36), 20, WHITE, anchor="center", alpha=a)

    # HUD
    def hud_info(self):
        if self.mode == "classic":
            ratio = min(1, self.score.level_score / self.level.goal)
            caption = f"Meta {min(self.score.level_score, self.level.goal)} / {self.level.goal}"
            return f"NÍVEL {self.level_no} de {self.db.level_count()}", ratio, caption, GREEN
        total = self.eaten + len(self.dots)
        return f"ONDA {self.level_no}", self.eaten / max(1, total), f"Docinhos {self.eaten} / {total}", PURPLE

    def draw_hearts(self, x, y, size, gap):
        for i in range(HEARTS):
            hx = x + i*gap
            if i < self.hearts: self.blit_glow(RED, hx, y+2, size*1.6, 60)
            self.draw_heart(hx, y, size, RED if i < self.hearts else (58, 50, 88))

    def draw_bar(self, rect, ratio, caption, color):
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.screen, (32, 32, 82), rect, border_radius=rect.h//2)
        if ratio > 0:
            fill = pygame.Rect(rect.x, rect.y, max(rect.h, int(rect.w*ratio)), rect.h)
            self.screen.blit(self.rounded_gradient(fill.size, lighten(color, .2), darken(color, .15), rect.h//2), fill)
        self.text(caption, rect.center, 13, WHITE, bold=True, anchor="center")

    def draw_multiplier(self, x, y, r):
        mult = self.score.multiplier
        if mult > 1:
            color = ORANGE if mult == 2 else PURPLE
            self.blit_glow(color, x, y, r*1.5, 110)
            pygame.draw.circle(self.screen, darken(color, .55), (x, y), r)
            frac = self.score.mult_left / max(1, self.score.mult_total)
            pygame.draw.arc(self.screen, color, (x-r, y-r, 2*r, 2*r), math.pi/2, math.pi/2 + 2*math.pi*frac, 5)
            self.text(f"×{mult}", (x, y), int(r*.8), WHITE, bold=True, anchor="center")
        else:
            pygame.draw.circle(self.screen, (30, 30, 76), (x, y), r)
            pygame.draw.circle(self.screen, (64, 64, 124), (x, y), r, 2)
            self.text("×1", (x, y), int(r*.72), MUTED, bold=True, anchor="center")

    def draw_streak(self, pos, anchor):
        streak = self.score.streak
        self.text(f"{streak} acerto{'s' if streak != 1 else ''}", pos, 18,
                  GREEN if streak >= 2 else WHITE, bold=True, anchor=anchor)

    def draw_hud(self):
        self.draw_sidebar() if self.layout.side else self.draw_bottom_hud()

    def draw_bottom_hud(self):
        hud = self.card(self.layout.hud)
        label, ratio, caption, color = self.hud_info()
        self.draw_hearts(hud.x + 30, hud.y + 24, 11, 32)
        self.text(f"{MODE_NAMES[self.mode].upper()} · {label}", (hud.x + 18, hud.y + 44), 14, MUTED)
        self.text(self.player_name, (hud.x + 18, hud.y + 62), 12, darken(MUTED, .25))
        cx = hud.centerx - 10
        self.text("PONTOS", (cx, hud.y + 6), 12, MUTED, anchor="midtop")
        self.text(thousands(self.score.score), (cx, hud.y + 32), 28, YELLOW, bold=True, anchor="center")
        self.draw_bar((cx - 130, hud.y + 52, 260, 18), ratio, caption, color)
        self.draw_multiplier(hud.right - 46, hud.centery, 27)
        rx = hud.right - 88
        self.text("SEQUÊNCIA", (rx, hud.y + 10), 12, MUTED, anchor="topright")
        self.draw_streak((rx, hud.y + 26), "topright")
        self.text("Setas/WASD · ESC pausa · F11 tela cheia", (rx, hud.y + 58), 12, darken(MUTED, .2), anchor="topright")

    def draw_sidebar(self):
        hud = self.layout.hud
        x, w, cx = hud.x, hud.w, hud.centerx
        label, ratio, caption, color = self.hud_info()
        self.glow_text("PAC-LÓGICA", (cx, hud.y + 26), 32, YELLOW)
        self.text(f"{self.player_name} · {MODE_NAMES[self.mode]}", (cx, hud.y + 62), 15, MUTED, anchor="center")

        c = self.card((x, hud.y + 86, w, 78), "VIDAS")
        self.draw_hearts(c.x + 34, c.y + 48, 13, 40)

        c = self.card((x, hud.y + 176, w, 126), "PONTOS")
        self.text(thousands(self.score.score), (cx, c.y + 56), 44, YELLOW, bold=True, anchor="center")
        self.draw_bar((c.x + 16, c.y + 90, w - 32, 20), ratio, caption, color)

        c = self.card((x, hud.y + 314, w, 94), "MULTIPLICADOR · SEQUÊNCIA")
        self.draw_multiplier(c.x + 50, c.y + 56, 26)
        self.text("Acertos seguidos", (c.x + 96, c.y + 40), 13, MUTED)
        self.draw_streak((c.x + 96, c.y + 58), "topleft")

        c = self.card((x, hud.y + 420, w, 150), "ESCALA DE NÍVEIS" if self.mode == "classic" else "ONDA")
        if self.mode == "classic":
            self.draw_level_scale(cx, c.y + 54, self.level_no - 1, step=min(34, (w - 40)//7), r=11, size=12)
        else:
            self.text(label, (cx, c.y + 54), 28, PURPLE, bold=True, anchor="center")
        topics = " · ".join(TOPIC_NAMES.get(t, t) for t in self.level.topic_list)
        self.paragraph(topics, (cx, c.y + 84), 14, w - 32, WHITE, spacing=2)

        hint_y = hud.bottom - 86
        for line in ("Setas ou WASD: mover", "ESC: pausar · F11: tela cheia", "Teclas 1 a 4: responder"):
            self.text(line, (cx, hint_y), 13, darken(MUTED, .15), anchor="midtop"); hint_y += 22

    def draw_level_scale(self, cx, y, done, step=64, r=16, size=16):
        """Escala de níveis: concluídos em verde, o atual/próximo em amarelo."""
        total = self.db.level_count()
        x0 = cx - step * (total - 1) / 2
        for i in range(total - 1):
            pygame.draw.line(self.screen, GREEN if i < done else (58, 58, 116),
                             (x0 + i*step, y), (x0 + (i+1)*step, y), max(2, r//4))
        for i in range(total):
            x, n = x0 + i*step, i + 1
            if n <= done:
                pygame.draw.circle(self.screen, GREEN, (int(x), y), r)
                self.text(n, (x, y), size, (12, 44, 26), bold=True, anchor="center")
            elif n == done + 1:
                self.blit_glow(YELLOW, x, y, r*2.1, 130)
                pygame.draw.circle(self.screen, YELLOW, (int(x), y), r + 2)
                self.text(n, (x, y), size + 1, (44, 32, 0), bold=True, anchor="center")
            else:
                pygame.draw.circle(self.screen, (30, 30, 76), (int(x), y), r)
                pygame.draw.circle(self.screen, (70, 70, 136), (int(x), y), r, 2)
                self.text(n, (x, y), size - 1, MUTED, anchor="center")

    # Telas
    def draw(self):
        self.buttons = []
        self.mouse = pygame.mouse.get_pos()
        if self.state in ("menu", "ranking"):
            self._backdrop = None
            self.screen.blit(self.menu_background, (0, 0))
            self.draw_menu() if self.state == "menu" else self.draw_ranking()
        elif self.state in OVERLAYS:
            if self._backdrop is None:
                # O jogo fica parado sob as janelas: desfoca uma única vez.
                self.draw_world()
                self.draw_hud()
                backdrop = blur(self.screen.copy(), 3)
                shade = pygame.Surface(self.layout.size, pygame.SRCALPHA)
                shade.fill((6, 6, 22, 150))
                backdrop.blit(shade, (0, 0))
                self._backdrop = backdrop
            self.screen.blit(self._backdrop, (0, 0))
            {"pause": self.draw_pause, "quiz": self.draw_quiz, "feedback": self.draw_feedback,
             "level_up": self.draw_level_up, "over": self.draw_game_over,
             "victory": self.draw_game_over}[self.state]()
        else:
            self._backdrop = None
            self.draw_world()
            self.draw_hud()
        self.update_cursor()

    def draw_chase(self, y):
        t, w = pygame.time.get_ticks(), self.layout.w
        x = (t*.16) % (w + 260) - 130
        for dx in range(40, w, 44):
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
        t, cx, W = pygame.time.get_ticks(), self.cx, self.layout.w
        self.glow_text("PAC-LÓGICA", (cx, 64), 64, YELLOW)
        self.text("Lógica proposicional no labirinto", (cx, 112), 18, MUTED, anchor="center")
        self.draw_chase(152)
        # Nome do jogador
        self.text("NOME DO JOGADOR", (cx, 186), 12, MUTED, bold=True, anchor="center")
        box = pygame.Rect(cx-180, 200, 360, 46)
        self.screen.blit(self.rounded_gradient(box.size, (14, 14, 44), (20, 20, 56), 14), box)
        pygame.draw.rect(self.screen, mix(PANEL, NEON, .8), box, 2, border_radius=14)
        if self.player_name:
            r = self.text(self.player_name, box.center, 22, WHITE, anchor="center")
            caret_x = r.right + 3
        else:
            self.text("Digite seu nome", box.center, 20, darken(MUTED, .3), anchor="center")
            caret_x = box.centerx + self.text_width("Digite seu nome", 20)//2 + 3
        if (t//500) % 2 == 0:
            pygame.draw.line(self.screen, YELLOW, (caret_x, box.y+12), (caret_x, box.bottom-12), 2)
        stats = self.player_stats()
        if stats and stats["games"]:
            info = (f"Partidas: {stats['games']} · Melhor nível tradicional: {stats['best_level'] or '-'}"
                    f" · Recorde tradicional: {thousands(stats['best_classic'])}"
                    f" · Recorde arcade: {thousands(stats['best_arcade'])}")
        else:
            info = "Digite seu nome e escolha um modo de jogo"
        self.text(info, (cx, 264), 14, MUTED, anchor="center")
        # Modos de jogo
        levels = self.db.level_count()
        cards = [
            ("classic", "Tradicional", f"Atinja a meta de pontos para subir de nível. São {levels} níveis, "
                                       "das regras dos conectivos até as tabelas-verdade.", GREEN),
            ("arcade", "Arcade", "Sem fases: some o máximo de pontos até perder todos os corações "
                                 "e entre no ranking de jogadores.", ORANGE),
        ]
        cw = min(440, (W - 100)//2 - 12)
        for i, (action, title, desc, color) in enumerate(cards):
            rect = pygame.Rect(cx - cw - 12 + i*(cw + 24), 290, cw, 172)
            hover = rect.collidepoint(self.mouse)
            body = rect.move(0, -3) if hover else rect
            if hover: self.blit_glow(color, body.centerx, body.centery, 200, 45)
            pygame.draw.rect(self.screen, (6, 6, 20), rect.move(0, 6), border_radius=20)
            self.screen.blit(self.rounded_gradient(body.size, mix(PANEL, color, .1 if hover else .05),
                                                   darken(PANEL, .15), 20), body)
            pygame.draw.rect(self.screen, color if hover else mix(PANEL, color, .55), body, 2, border_radius=20)
            if action == "classic":
                self.draw_pacman_at(body.x+36, body.y+36, 0, 15, .2)
            else:
                self.draw_ghost_at(body.x+36, body.y+36, GHOST_STARTS[1][2], 0, 1, 15)
            self.text(title, (body.x+64, body.y+36), 28, WHITE, bold=True, anchor="midleft")
            self.paragraph(desc, (body.x+22, body.y+66), 15, body.w-44, MUTED, anchor="topleft", spacing=3)
            pill = pygame.Rect(body.right-112, body.bottom-46, 94, 32)
            self.screen.blit(self.rounded_gradient(pill.size, lighten(color, .1), darken(color, .2 if hover else .4), 16), pill)
            self.text("JOGAR", pill.center, 15, (12, 20, 30) if hover else WHITE, bold=True, anchor="center")
            self.buttons.append((rect, action))
        # Legenda das frutas
        self.text("FRUTAS ESPECIAIS", (cx, 486), 12, MUTED, bold=True, anchor="center")
        step = min(170, (W - 120)//len(FRUITS))
        for i, f in enumerate(FRUITS):
            x = cx + (i - (len(FRUITS)-1)/2) * step
            self.blit_glow(f.color, x, 522, 30, 50)
            self.draw_fruit(f.key, x, 522, 1.05)
            self.text(f.name, (x, 554), 14, WHITE, anchor="center")
            self.text(f.label(), (x, 572), 14, f.color, bold=True, anchor="center")
        # Ranking, proporção da tela e sair
        self.button((cx - 300, 616, 170, 46), "Ranking", "ranking", ACCENT)
        self.text("PROPORÇÃO DA TELA", (cx, 603), 11, MUTED, bold=True, anchor="center")
        for i, aspect in enumerate(ASPECTS):
            active = self.layout.aspect == aspect
            self.button((cx - 104 + i*108, 616, 100, 46), aspect, ("aspect", aspect),
                        ACCENT if active else (44, 46, 96), 18)
        self.button((cx + 130, 616, 170, 46), "Sair", "quit", BAD_BTN)
        self.text("Respostas: teclas 1 a 4 · Pausa: ESC · Tela cheia: F11", (cx, 694), 12,
                  darken(MUTED, .2), anchor="center")

    def draw_ranking(self):
        cx = self.cx
        self.glow_text("RANKING", (cx, 54), 52, YELLOW)
        for i, mode in enumerate(("arcade", "classic")):
            active = self.ranking_mode == mode
            self.button((cx - 190 + i*200, 96, 180, 42), MODE_NAMES[mode], ("tab", mode),
                        ACCENT if active else (44, 46, 96), 18)
        tw = min(self.layout.w - 120, 860)
        table = self.panel((cx - tw//2, 160, tw, 432))
        level_label = "NÍVEL" if self.ranking_mode == "classic" else "ONDA"
        cols = {"#": table.x + 40, "player": table.x + 82, "score": table.x + int(tw*.6),
                "level": table.x + int(tw*.73), "date": table.right - 30}
        hy = table.y + 28
        self.text("#", (cols["#"], hy), 12, MUTED, bold=True, anchor="center")
        self.text("JOGADOR", (cols["player"], hy), 12, MUTED, bold=True, anchor="midleft")
        self.text("PONTOS", (cols["score"], hy), 12, MUTED, bold=True, anchor="midright")
        self.text(level_label, (cols["level"], hy), 12, MUTED, bold=True, anchor="center")
        self.text("DATA", (cols["date"], hy), 12, MUTED, bold=True, anchor="midright")
        pygame.draw.line(self.screen, mix(PANEL, PANEL_EDGE, .5), (table.x+20, hy+18), (table.right-20, hy+18), 1)
        rows = self.db.top_scores(self.ranking_mode, 10)
        if not rows:
            self.text("Nenhuma partida registrada ainda. Seja o primeiro!", table.center, 18, MUTED, anchor="center")
        for i, row in enumerate(rows):
            y = hy + 52 + i*36
            if row["id"] == self.last_score_id:
                hl = pygame.Rect(table.x+14, y-16, table.w-28, 32)
                self.screen.blit(self.rounded_gradient(hl.size, (64, 72, 170), (48, 54, 140), 10), hl)
            elif i % 2:
                pygame.draw.rect(self.screen, lighten(PANEL, .03), (table.x+14, y-16, table.w-28, 32), border_radius=10)
            if i < 3:
                pygame.draw.circle(self.screen, MEDALS[i], (cols["#"], y), 13)
                self.text(i+1, (cols["#"], y), 15, (34, 24, 10), bold=True, anchor="center")
            else:
                self.text(i+1, (cols["#"], y), 16, MUTED, anchor="center")
            self.text(row["player"], (cols["player"], y), 18, WHITE, anchor="midleft")
            self.text(thousands(row["score"]), (cols["score"], y), 18, YELLOW, bold=True, anchor="midright")
            self.text(row["level"], (cols["level"], y), 17, WHITE, anchor="center")
            try:
                date = datetime.fromisoformat(row["created_at"]).strftime("%d/%m/%y")
            except ValueError:
                date = "-"
            self.text(date, (cols["date"], y), 15, MUTED, anchor="midright")
        self.button((cx-120, 622, 240, 48), "Voltar ao menu", "menu", ACCENT)

    def quiz_panel(self, height, accent=PANEL_EDGE):
        """Painel centralizado com a altura do conteúdo; devolve o topo do conteúdo."""
        w = min(780, self.layout.w - 80)
        h = min(height, self.layout.h - 40)
        rect = self.panel((self.cx - w//2, (self.layout.h - h)//2, w, h), accent)
        return rect.y

    LINE_STYLES = {"big": (44, YELLOW), "text": (22, WHITE), "accent": (22, YELLOW), "muted": (17, MUTED)}

    def box_rows(self, lines, width):
        rows = []
        for text, style in lines:
            size, color = self.LINE_STYLES[style]
            wrapped = self.wrap(text, size, width - 48) if text else [""]
            rows += [(line, size, color, size + 10 if line else 8) for line in wrapped]
        return rows, max(84, sum(r[3] for r in rows) + 36)

    def question_box(self, lines, top, width=620):
        cx = self.cx
        rows, height = self.box_rows(lines, width)
        box = pygame.Rect(cx - width//2, top, width, height)
        self.screen.blit(self.rounded_gradient(box.size, (12, 12, 40), (18, 18, 52), 18), box)
        pygame.draw.rect(self.screen, mix(PANEL, NEON, .7), box, 2, border_radius=18)
        y = box.centery - sum(r[3] for r in rows)/2
        for line, size, color, h in rows:
            if line: self.text(line, (cx, y + h/2), size, color, anchor="center")
            y += h
        return box.bottom

    def option_rects(self, options, top):
        cx, n = self.cx, len(options)
        widest = max(self.text_width(o, 20) for o in options)
        if widest > 250 or (n == 3 and widest > 180):
            return [((cx - 310, top + i*64, 620, 54), 20) for i in range(n)]
        if n == 4:
            return [((cx - 310 + (i % 2)*320, top + (i // 2)*82, 300, 68), 24) for i in range(n)]
        w = (640 - 16*(n-1)) // n
        return [((cx - 320 + i*(w+16), top, w, 68), 22) for i in range(n)]

    def draw_options(self, options, top):
        for i, (label, (rect, size)) in enumerate(zip(options, self.option_rects(options, top))):
            self.button(rect, label, ("answer", i), ACCENT, size, str(i+1))

    def draw_timer(self, y):
        cx, left = self.cx, max(0, self.quiz_left)
        secs = math.ceil(left / 1000)
        color = GREEN if secs > 8 else ORANGE if secs > 4 else RED
        bar = pygame.Rect(cx - 220, y, 440, 14)
        pygame.draw.rect(self.screen, (32, 32, 82), bar, border_radius=7)
        if left > 0:
            fill = pygame.Rect(bar.x, bar.y, max(14, int(bar.w*left/QUIZ_TIME)), bar.h)
            self.screen.blit(self.rounded_gradient(fill.size, lighten(color, .2), darken(color, .1), 7), fill)
        self.text(f"{secs}s", (bar.right + 14, bar.centery), 18, color, bold=True, anchor="midleft")

    def draw_quiz(self):
        q, cx = self.question, self.cx
        revive = self.quiz_mode != "eat"
        box_h = self.box_rows(q["lines"], 620)[1]
        opts_h = max(pygame.Rect(r).bottom for r, _ in self.option_rects(q["options"], 0))
        top = self.quiz_panel(168 + box_h + 24 + opts_h + 74, RED if revive else PANEL_EDGE)
        if not revive:
            self.glow_text("QUESTÃO DE LÓGICA", (cx, top + 44), 32, YELLOW)
            stake = f"Acerte e ganhe {plural(self.score.preview_correct(), 'ponto')} · Errar custa 1 coração"
            if self.score.multiplier > 1: stake += f" · ×{self.score.multiplier} ativo"
        else:
            self.glow_text("CHANCE DE REVIVER", (cx, top + 44), 32, RED)
            stake = f"Acerte para voltar com {REVIVE_HEARTS} corações. Só há uma chance!"
        self.text(stake, (cx, top + 80), 16, MUTED, anchor="center")
        self.draw_timer(top + 102)
        self.text(q["prompt"], (cx, top + 146), 21, WHITE, anchor="center")
        bottom = self.question_box(q["lines"], top + 168)
        self.draw_options(q["options"], bottom + 24)
        n = len(q["options"])
        keys = "as teclas 1 ou 2" if n == 2 else f"as teclas 1 a {n}"
        self.text(f"Clique na resposta ou use {keys}", (cx, bottom + 24 + opts_h + 34), 14,
                  darken(MUTED, .15), anchor="center")

    def truth_table(self, headers, rows, top, n_inputs):
        cx = self.cx
        widths = [max(58, self.text_width(h, 20) + 32) for h in headers]
        total, rh = sum(widths), 34
        x0 = cx - total//2
        bottom = top + rh*(len(rows)+1)
        self.screen.blit(self.rounded_gradient((total, bottom - top), (26, 28, 74), (22, 24, 64), 12), (x0, top))
        pygame.draw.rect(self.screen, (44, 50, 124), (x0, top, total, rh),
                         border_top_left_radius=12, border_top_right_radius=12)
        x = x0
        for h, w in zip(headers, widths):
            self.text(h, (x + w/2, top + rh/2), 20, WHITE, anchor="center"); x += w
        for i, row in enumerate(rows):
            y = top + rh*(i+1)
            if i % 2: pygame.draw.rect(self.screen, (32, 34, 86), (x0 + 2, y, total - 4, rh))
            x = x0
            for v, w in zip(row, widths):
                self.text("V" if v else "F", (x + w/2, y + rh/2), 20, GREEN if v else RED, bold=True, anchor="center")
                x += w
        split = x0 + sum(widths[:n_inputs])
        pygame.draw.line(self.screen, mix(PANEL, NEON, .8), (split, top), (split, bottom-1), 2)
        pygame.draw.rect(self.screen, mix(PANEL, NEON, .8), (x0, top, total, bottom-top), 2, border_radius=12)
        return bottom

    def draw_feedback(self):
        q, ok, cx = self.question, self.feedback, self.cx
        table = q.get("table")
        explanation_h = len(self.wrap(q["explanation"], 17, 620)) * 27
        table_h = (len(table[1]) + 1) * 34 + 16 if table else 0
        top = self.quiz_panel(176 + explanation_h + table_h + 116, GREEN if ok else RED)
        title = "CORRETO!" if ok else "TEMPO ESGOTADO!" if self.timed_out else "ERROU!"
        self.glow_text(title, (cx, top + 52), 44, GREEN if ok else RED)
        if self.quiz_mode == "eat":
            sub = (f"+{plural(self.last_points, 'ponto')}", YELLOW) if ok else ("Você perdeu 1 coração.", RED)
        else:
            sub = (f"Você voltou com {REVIVE_HEARTS} corações!", GREEN) if ok else ("Não foi dessa vez...", RED)
        self.text(sub[0], (cx, top + 100), 24, sub[1], bold=True, anchor="center")
        self.text(f"Resposta correta: {q['options'][q['answer']]}", (cx, top + 144), 20, WHITE, anchor="center")
        y = self.paragraph(q["explanation"], (cx, top + 170), 17, 620, MUTED, spacing=4)
        if table:
            y = self.truth_table(table[0], table[1], y + 16, table[2])
        self.button((cx-130, y + 30, 260, 56), "Continuar (Enter)", "continue", GOOD_BTN if ok else ACCENT, 21)

    def draw_pause(self):
        cx = self.cx
        rect = self.panel((cx-210, 200, 420, 300))
        self.glow_text("PAUSADO", (cx, rect.y+56), 40, YELLOW)
        self.button((cx-130, rect.y+110, 260, 52), "Continuar", "resume", GOOD_BTN, 20)
        self.button((cx-130, rect.y+178, 260, 52), "Menu principal", "menu", ACCENT, 20)
        self.text("Voltar ao menu encerra a partida sem salvar.", (cx, rect.bottom-30), 13, MUTED, anchor="center")

    def draw_level_up(self):
        cx = self.cx
        rect = self.panel((cx-320, 80, 640, 560), GREEN)
        self.glow_text(f"NÍVEL {self.level_no} CONCLUÍDO!", (cx, rect.y+56), 38, GREEN)
        self.text("ESCALA DE NÍVEIS", (cx, rect.y+104), 12, MUTED, bold=True, anchor="center")
        self.draw_level_scale(cx, rect.y + 140, self.level_no)
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
        y = rect.y + 200
        for s, color, size, bold in lines:
            if not s: continue
            self.text(s, (cx, y), size, color, bold=bold, anchor="center")
            y += size + 22
        self.button((cx-140, rect.bottom-86, 280, 56), "Próximo nível", "next_level", GOOD_BTN, 22)

    def draw_game_over(self):
        cx, victory = self.cx, self.state == "victory"
        color = GREEN if victory else RED
        rect = self.panel((cx-320, 100, 640, 510), color)
        self.glow_text("VOCÊ VENCEU!" if victory else "FIM DE JOGO", (cx, rect.y+60), 48, color)
        sub = "Todos os níveis do modo tradicional concluídos!" if victory else self.player_name
        self.text(sub, (cx, rect.y+110), 20, WHITE, anchor="center")
        self.text("PONTUAÇÃO FINAL", (cx, rect.y+158), 12, MUTED, bold=True, anchor="center")
        self.glow_text(thousands(self.score.score), (cx, rect.y+204), 60, YELLOW)
        reached = f"Nível alcançado: {self.level_no}" if self.mode == "classic" else f"Onda alcançada: {self.level_no}"
        self.text(reached, (cx, rect.y+258), 20, WHITE, anchor="center")
        if self.last_rank:
            if self.last_rank == 1:
                self.text("NOVO RECORDE!", (cx, rect.y+304), 26, YELLOW, bold=True, anchor="center")
            self.text(f"{self.last_rank}º lugar no ranking {MODE_NAMES[self.mode]}",
                      (cx, rect.y+340), 19, MUTED, anchor="center")
        y = rect.bottom - 84
        self.button((cx-290, y, 190, 54), "Jogar novamente", "again", GOOD_BTN, 19)
        self.button((cx-85, y, 170, 54), "Ranking", "ranking", ACCENT, 19)
        self.button((cx+100, y, 190, 54), "Menu", "menu", (64, 68, 132), 19)
