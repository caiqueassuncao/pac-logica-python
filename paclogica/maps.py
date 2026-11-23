"""Mapas e layouts variados do Pac-Lógica.

Cada mapa é um desenho em texto com ROWS linhas e COLS colunas (ver config.py):

    #  parede
    .  caminho livre
    P  início do Pac-Man (vira caminho livre)
    1-4  início dos fantasmas 1 a 4 (viram caminho livre; a cor vem de GHOST_STARTS)

Para criar um mapa novo, copie um bloco de MAPS, desenhe o labirinto e rode os testes:
    python -m unittest tests.test_maps
Os testes avisam se o mapa tem tamanho errado, trechos isolados ou becos sem saída.
"""
from dataclasses import dataclass
from .config import ROWS, COLS, MAP, PLAYER_START, GHOST_STARTS


@dataclass(frozen=True)
class GameMap:
    name: str
    grid: tuple          # ROWS strings com "#" (parede) e "." (caminho)
    player_start: tuple  # (linha, coluna)
    ghost_starts: tuple  # ((linha, coluna, cor), ...) na mesma ordem de GHOST_STARTS


def parse_map(name, rows):
    """Converte o desenho em texto (com P e 1-4) em um GameMap."""
    grid, player, ghosts = [], None, {}
    for r, line in enumerate(rows):
        clean = []
        for c, ch in enumerate(line):
            if ch == "P":
                player = (r, c)
                ch = "."
            elif ch in "1234":
                ghosts[int(ch) - 1] = (r, c)
                ch = "."
            clean.append(ch)
        grid.append("".join(clean))
    ghost_starts = tuple((*ghosts[i], GHOST_STARTS[i][2]) for i in sorted(ghosts))
    return GameMap(name, tuple(grid), player, ghost_starts)


# O primeiro mapa é o labirinto original, mantido igual ao de config.py.
CLASSIC = GameMap("Clássico", tuple(MAP), PLAYER_START, tuple(GHOST_STARTS))

CORREDORES = parse_map("Corredores", [
    "#######################",
    "#1.........3.........2#",
    "#.#########.#########.#",
    "#.....................#",
    "#.##.#############.##.#",
    "#.##.#############.##.#",
    "#.....................#",
    "#.#########.#########.#",
    "#.....................#",
    "#.#########.#########.#",
    "#.....................#",
    "#.##.#############.##.#",
    "#.##.#############.##.#",
    "#.....................#",
    "#.#########.#########.#",
    "#4.........P..........#",
    "#######################",
])

PILARES = parse_map("Pilares", [
    "#######################",
    "#1.........3.........2#",
    "#.###.###.###.###.###.#",
    "#.....................#",
    "#.###.###.###.###.###.#",
    "#.....................#",
    "#.###.###.###.###.###.#",
    "#.....................#",
    "#.###.###.###.###.###.#",
    "#.....................#",
    "#.###.###.###.###.###.#",
    "#.....................#",
    "#.###.###.###.###.###.#",
    "#.....................#",
    "#.###.###.###.###.###.#",
    "#4.........P..........#",
    "#######################",
])

BLOCOS = parse_map("Blocos", [
    "#######################",
    "#1.........3.........2#",
    "#.####.####.####.####.#",
    "#.####.####.####.####.#",
    "#.....................#",
    "#.##.####.#.#.####.##.#",
    "#.##.####.#.#.####.##.#",
    "#.....................#",
    "#.####.####.####.####.#",
    "#.....................#",
    "#.##.####.#.#.####.##.#",
    "#.##.####.#.#.####.##.#",
    "#.....................#",
    "#.####.####.####.####.#",
    "#.####.####.####.####.#",
    "#4.........P..........#",
    "#######################",
])

ANEL = parse_map("Anel", [
    "#######################",
    "#1.........3.........2#",
    "#.#####.#######.#####.#",
    "#.#.................#.#",
    "#.#.###.#######.###.#.#",
    "#.#.#.............#.#.#",
    "#...#.###.#.#.###.#...#",
    "#.#.#.#.........#.#.#.#",
    "#.#.#.#.#######.#.#.#.#",
    "#.#.#.#.........#.#.#.#",
    "#...#.###.#.#.###.#...#",
    "#.#.#.............#.#.#",
    "#.#.###.#######.###.#.#",
    "#.#.................#.#",
    "#.#####.#######.#####.#",
    "#4.........P..........#",
    "#######################",
])

# Ordem em que os mapas aparecem: nível 1 = Clássico, nível 2 = Corredores...
MAPS = [CLASSIC, CORREDORES, PILARES, BLOCOS, ANEL]


def map_for_level(level_no):
    """Mapa de cada nível (ou onda, no arcade). Depois do último, volta ao primeiro."""
    return MAPS[(level_no - 1) % len(MAPS)]
