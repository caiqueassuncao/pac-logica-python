from dataclasses import dataclass
from .config import TILE, YELLOW

@dataclass
class Entity:
    r: int
    c: int
    step: int
    dr: int = 0
    dc: int = 0
    pr: int = -1
    pc: int = -1
    acc: int = 0
    color: tuple = YELLOW

    def __post_init__(self):
        if self.pr < 0: self.pr, self.pc = self.r, self.c

    def pixel(self):
        t = min(1, self.acc / self.step)
        return ((self.pc + (self.c-self.pc)*t + .5)*TILE,
                (self.pr + (self.r-self.pr)*t + .5)*TILE)

