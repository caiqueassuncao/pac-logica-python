from .config import CANDY_COLORS
from .maps import MAPS
import random

# Mapa em uso. O jogo troca chamando set_map() ao iniciar cada nível.
_current = MAPS[0]

def set_map(game_map):
    global _current
    _current = game_map

def current_map():
    return _current

def player_start():
    return _current.player_start

def ghost_starts():
    return _current.ghost_starts

def free(row, col):
    grid = _current.grid
    return 0 <= row < len(grid) and 0 <= col < len(grid[0]) and grid[row][col] == "."

def free_cells():
    grid = _current.grid
    return [(r,c) for r in range(len(grid)) for c in range(len(grid[0])) if free(r,c)]

def create_dots(count, excluded=()):
    excluded = {_current.player_start} | {(r,c) for r,c,_ in _current.ghost_starts} | set(excluded)
    cells = [cell for cell in free_cells() if cell not in excluded]
    random.shuffle(cells)
    return {cell: random.choice(CANDY_COLORS) for cell in cells[:count]}

def random_free_cell(excluded=(), far_from=None, min_distance=0):
    cells = [cell for cell in free_cells() if cell not in excluded and
            (far_from is None or abs(cell[0]-far_from[0]) + abs(cell[1]-far_from[1]) >= min_distance)]
    return random.choice(cells) if cells else None
