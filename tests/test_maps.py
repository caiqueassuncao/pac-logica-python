import os
import unittest
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from paclogica.database import Database
from paclogica.game import PacLogica

from paclogica.config import ROWS, COLS, GHOST_STARTS
from paclogica.maps import MAPS, map_for_level
from paclogica import maze

MIN_FREE_CELLS = 120  # espaço de sobra para docinhos, frutas e fantasmas


def free_cells(m):
    return {(r, c) for r in range(ROWS) for c in range(COLS) if m.grid[r][c] == "."}


def neighbors(cell, cells):
    r, c = cell
    return [n for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)) if n in cells]


class MapsTest(unittest.TestCase):
    def test_there_are_several_maps_with_unique_names(self):
        self.assertGreaterEqual(len(MAPS), 4)
        self.assertEqual(len({m.name for m in MAPS}), len(MAPS))

    def test_size_and_border(self):
        for m in MAPS:
            with self.subTest(mapa=m.name):
                self.assertEqual(len(m.grid), ROWS)
                for r, line in enumerate(m.grid):
                    self.assertEqual(len(line), COLS, f"linha {r} com {len(line)} colunas")
                    self.assertTrue(set(line) <= {"#", "."}, f"caractere inválido na linha {r}")
                self.assertEqual(set(m.grid[0]), {"#"})
                self.assertEqual(set(m.grid[-1]), {"#"})
                for line in m.grid:
                    self.assertEqual((line[0], line[-1]), ("#", "#"))

    def test_starts_are_on_free_cells(self):
        for m in MAPS:
            with self.subTest(mapa=m.name):
                cells = free_cells(m)
                self.assertIn(m.player_start, cells)
                self.assertEqual(len(m.ghost_starts), len(GHOST_STARTS))
                for (r, c, color), (_, _, expected) in zip(m.ghost_starts, GHOST_STARTS):
                    self.assertIn((r, c), cells)
                    self.assertEqual(color, expected)

    def test_enough_room_to_play(self):
        for m in MAPS:
            with self.subTest(mapa=m.name):
                self.assertGreaterEqual(len(free_cells(m)), MIN_FREE_CELLS)

    def test_every_free_cell_is_reachable(self):
        for m in MAPS:
            with self.subTest(mapa=m.name):
                cells = free_cells(m)
                seen, queue = {m.player_start}, deque([m.player_start])
                while queue:
                    for n in neighbors(queue.popleft(), cells):
                        if n not in seen:
                            seen.add(n)
                            queue.append(n)
                self.assertEqual(cells - seen, set(), "há trechos isolados do mapa")

    def test_no_dead_ends(self):
        # Beco sem saída = casa livre com só um vizinho: o fantasma ficaria preso indo e voltando.
        for m in MAPS:
            with self.subTest(mapa=m.name):
                cells = free_cells(m)
                dead = [c for c in cells if len(neighbors(c, cells)) < 2]
                self.assertEqual(dead, [])

    def test_map_for_level_cycles_through_all_maps(self):
        self.assertIs(map_for_level(1), MAPS[0])
        self.assertIs(map_for_level(len(MAPS)), MAPS[-1])
        self.assertIs(map_for_level(len(MAPS) + 1), MAPS[0])
        self.assertEqual({map_for_level(n).name for n in range(1, len(MAPS) + 1)},
                         {m.name for m in MAPS})

    def test_maze_follows_the_selected_map(self):
        try:
            for m in MAPS:
                maze.set_map(m)
                self.assertIs(maze.current_map(), m)
                self.assertEqual(maze.player_start(), m.player_start)
                self.assertEqual(set(maze.free_cells()), free_cells(m))
                dots = maze.create_dots(12)
                self.assertEqual(len(dots), 12)
                self.assertNotIn(m.player_start, dots)
        finally:
            maze.set_map(MAPS[0])


class GameUsesMapsTest(unittest.TestCase):
    def setUp(self):
        self.game = PacLogica(Database(":memory:"))
        self.game.player_name = "Teste"

    def tearDown(self):
        maze.set_map(MAPS[0])
        self.game.db.close()
        pygame.quit()

    def test_each_level_starts_on_its_own_map(self):
        g = self.game
        g.new_game("classic")
        for level in range(1, g.db.level_count() + 1):
            g.level_no = level
            g.start_level()
            expected = map_for_level(level)
            self.assertIs(g.map, expected)
            self.assertIs(maze.current_map(), expected)
            self.assertEqual((g.player.r, g.player.c), expected.player_start)
            for ghost, (r, c, _) in zip(g.ghosts, expected.ghost_starts):
                self.assertEqual((ghost.r, ghost.c), (r, c))
            self.assertTrue(set(g.dots) <= free_cells(expected))
            g.draw()

    def test_arcade_wave_changes_map(self):
        g = self.game
        g.new_game("arcade")
        first = g.map
        g.dots.clear()
        g.check_progress()
        self.assertIsNot(g.map, first)
        self.assertEqual(g.state, "play")

    def test_new_game_goes_back_to_first_map(self):
        g = self.game
        g.new_game("classic")
        g.level_no = 3
        g.start_level()
        g.new_game("classic")
        self.assertIs(g.map, MAPS[0])


if __name__ == "__main__":
    unittest.main()
