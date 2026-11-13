from .config import ROWS, COLS, MAP, PLAYER_START, GHOST_STARTS, TOTAL_DOTS, CANDY_COLORS
import random

def free(row, col):
    return 0 <= row < ROWS and 0 <= col < COLS and MAP[row][col] == "."

def create_dots():
    excluded = {PLAYER_START} | {(r,c) for r,c,_ in GHOST_STARTS}
    cells = [(r,c) for r in range(ROWS) for c in range(COLS)
             if free(r,c) and (r,c) not in excluded]
    random.shuffle(cells)
    return {cell: random.choice(CANDY_COLORS) for cell in cells[:TOTAL_DOTS]}
