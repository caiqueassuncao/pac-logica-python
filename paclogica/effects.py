import math
import random
from dataclasses import dataclass

@dataclass
class Popup:
    text: str
    x: float
    y: float
    color: tuple
    life: int = 1100
    age: int = 0
    size: int = 22

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: tuple
    life: int
    age: int = 0

@dataclass
class Banner:
    text: str
    color: tuple
    life: int = 1800
    age: int = 0
    sub: str = ""

class Effects:
    """Efeitos visuais passageiros: textos flutuantes, partículas e faixas de aviso."""

    def __init__(self):
        self.clear()

    def clear(self):
        self.popups, self.particles, self.banner = [], [], None

    def popup(self, text, x, y, color, size=22):
        self.popups.append(Popup(text, x, y, color, size=size))

    def burst(self, x, y, color, count=14, speed=.16):
        for _ in range(count):
            a = random.uniform(0, 2*math.pi)
            v = random.uniform(.3, 1) * speed
            self.particles.append(Particle(x, y, math.cos(a)*v, math.sin(a)*v, color, random.randint(350, 700)))

    def announce(self, text, color, life=2200, sub=""):
        self.banner = Banner(text, color, life, sub=sub)

    def update(self, dt):
        for p in self.popups:
            p.age += dt
            p.y -= dt * .035
        for p in self.particles:
            p.age += dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= .96; p.vy *= .96
        self.popups = [p for p in self.popups if p.age < p.life]
        self.particles = [p for p in self.particles if p.age < p.life]
        if self.banner:
            self.banner.age += dt
            if self.banner.age >= self.banner.life:
                self.banner = None
