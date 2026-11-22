import random
from dataclasses import dataclass
from .config import CANDY_POINTS

@dataclass(frozen=True)
class FruitKind:
    key: str
    name: str
    bonus: int = 0
    multiplier: int = 1
    duration: int = 0
    weight: int = 1
    color: tuple = (255, 255, 255)

    def label(self):
        if self.multiplier > 1:
            return f"×{self.multiplier} por {self.duration // 1000}s"
        return f"+{self.bonus} pontos"

FRUITS = [
    FruitKind("cereja", "Cereja", bonus=2, weight=5, color=(255, 70, 90)),
    FruitKind("morango", "Morango", bonus=3, weight=3, color=(255, 90, 110)),
    FruitKind("laranja", "Laranja", multiplier=2, duration=12000, weight=3, color=(255, 160, 50)),
    FruitKind("uva", "Uva", multiplier=3, duration=9000, weight=2, color=(170, 100, 255)),
    FruitKind("melancia", "Melancia", bonus=5, weight=1, color=(90, 220, 110)),
]

def random_fruit(rng=random):
    return rng.choices(FRUITS, weights=[f.weight for f in FRUITS])[0]

def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"

class Scoreboard:
    """Pontuação da partida: total, pontos do nível atual, multiplicador e sequência de acertos."""

    def __init__(self):
        self.score = 0
        self.level_score = 0
        self.multiplier = 1
        self.mult_left = 0
        self.mult_total = 0
        self.streak = 0

    def add(self, base):
        points = base * self.multiplier
        self.score += points
        self.level_score += points
        return points

    def preview_correct(self):
        return CANDY_POINTS * self.multiplier

    def correct_answer(self):
        self.streak += 1
        return self.add(CANDY_POINTS)

    def wrong_answer(self):
        self.streak = 0

    def eat_fruit(self, kind):
        points = self.add(kind.bonus) if kind.bonus else 0
        if kind.multiplier > 1:
            if kind.multiplier >= self.multiplier:
                self.multiplier = kind.multiplier
                self.mult_left = self.mult_total = kind.duration
            else:
                # Multiplicador menor que o ativo apenas prolonga o atual.
                self.mult_left = min(self.mult_total, self.mult_left + kind.duration // 2)
        return points

    def tick(self, dt):
        if self.mult_left > 0:
            self.mult_left -= dt
            if self.mult_left <= 0:
                self.multiplier, self.mult_left, self.mult_total = 1, 0, 0

    def new_level(self):
        self.level_score = 0
