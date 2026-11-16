from .config import ROWS, COLS, MAP, PLAYER_START, GHOST_STARTS, CANDY_COLORS
import random

def free(row, col):
    return 0 <= row < ROWS and 0 <= col < COLS and MAP[row][col] == "."

def free_cells():
    return [(r,c) for r in range(ROWS) for c in range(COLS) if free(r,c)]

def create_dots(count, excluded=()):
    excluded = {PLAYER_START} | {(r,c) for r,c,_ in GHOST_STARTS} | set(excluded)
    cells = [cell for cell in free_cells() if cell not in excluded]
    random.shuffle(cells)
    return {cell: random.choice(CANDY_COLORS) for cell in cells[:count]}

def random_free_cell(excluded=(), far_from=None, min_distance=0):
    cells = [cell for cell in free_cells() if cell not in excluded and
            (far_from is None or abs(cell[0]-far_from[0]) + abs(cell[1]-far_from[1]) >= min_distance)]
    return random.choice(cells) if cells else None
