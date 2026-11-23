import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from paclogica.database import Database
from paclogica.entities import Fruit
from paclogica.game import PacLogica
from paclogica.scoring import FRUITS

STATES = ("menu", "ranking", "play", "pause", "quiz", "feedback", "level_up", "over")

class GameTest(unittest.TestCase):
    def setUp(self):
        self.game = PacLogica(Database(":memory:"))
        self.game.player_name = "Teste"

    def tearDown(self):
        self.game.db.close()
        pygame.quit()

    def frames(self, n=30):
        for _ in range(n):
            self.game.update(16)
            self.game.draw()

    def answer_current(self, correct=True):
        q = self.game.question
        self.game.answer(q["answer"] if correct else (q["answer"] + 1) % len(q["options"]))
        self.game.continue_after_feedback()

    def test_every_screen_renders(self):
        g = self.game
        g.draw()
        g.new_game("classic")
        for state in STATES:
            if state in ("quiz", "feedback"):
                g.ask("eat")
                if state == "feedback": g.answer(g.question["answer"])
            g.state = state
            g.draw()

    def test_text_input_is_active_only_in_menu(self):
        g = self.game
        with patch("pygame.key.start_text_input") as start, patch("pygame.key.stop_text_input") as stop:
            g.handle_events()
            start.assert_called_once_with()
            self.assertTrue(g._text_input_active)

            g.state = "play"
            g.handle_events()
            stop.assert_called_once_with()
            self.assertFalse(g._text_input_active)

    def test_both_aspects_render_and_switch(self):
        g = self.game
        other = "4:3" if g.layout.aspect == "16:9" else "16:9"
        for aspect in (other, g.layout.aspect, other):
            g.do(("aspect", aspect))
            self.assertEqual(g.screen.get_size(), g.layout.size)
            self.assertEqual(g.db.get_setting("aspect"), aspect)
            self.assertTrue(g.screen.get_rect().contains(g.layout.world))
            self.assertTrue(g.screen.get_rect().contains(g.layout.hud))
            self.assertFalse(g.layout.world.colliderect(g.layout.hud))
            g.state = "menu"; g.draw()
            g.new_game("classic")
            g.draw()
            g.ask("eat"); g.draw()

    def test_reaching_goal_levels_up(self):
        g = self.game
        g.new_game("classic")
        g.score.add(g.level.goal)
        g.check_progress()
        self.assertEqual(g.state, "level_up")
        g.do("next_level")
        self.assertEqual((g.level_no, g.state, g.score.level_score), (2, "play", 0))

    def test_correct_answer_scores_one_point(self):
        g = self.game
        g.new_game("classic")
        g.ask("eat")
        self.answer_current(True)
        self.assertEqual(g.score.score, 1)
        self.assertEqual(g.state, "play")

    def test_question_times_out(self):
        g = self.game
        g.new_game("classic")
        g.ask("eat")
        g.update(14000)
        self.assertEqual(g.state, "quiz")
        g.update(1000)
        self.assertEqual(g.state, "feedback")
        self.assertTrue(g.timed_out)
        self.assertFalse(g.feedback)
        g.draw()
        g.continue_after_feedback()
        self.assertEqual(g.hearts, 2)

    def test_level_one_asks_connective_rules(self):
        g = self.game
        g.new_game("classic")
        for _ in range(20):
            g.ask("eat")
            self.assertEqual(g.question["topic"], "conectivos")

    def test_fruit_with_multiplier(self):
        g = self.game
        g.new_game("arcade")
        uva = next(f for f in FRUITS if f.key == "uva")
        g.fruit = Fruit(uva, (g.player.r, g.player.c - 1), 5000)
        g.player.dr, g.player.dc = 0, -1
        g.dots.pop((g.player.r, g.player.c - 1), None)
        g.step_player()
        self.assertEqual(g.score.multiplier, 3)
        self.assertIsNone(g.fruit)

    def test_arcade_clears_board_into_next_wave(self):
        g = self.game
        g.new_game("arcade")
        g.dots.clear()
        g.check_progress()
        self.assertEqual((g.level_no, g.state), (2, "play"))
        self.assertTrue(g.dots)

    def test_game_over_saves_ranking(self):
        g = self.game
        g.new_game("arcade")
        g.score.add(321)
        g.hearts = 1
        g.ask("eat")
        self.answer_current(False)
        self.assertEqual(g.state, "quiz")  # chance de reviver
        self.answer_current(False)
        self.assertEqual(g.state, "over")
        self.assertEqual(g.last_rank, 1)
        self.assertEqual(g.db.top_scores("arcade")[0]["score"], 321)

    def test_play_loop_runs(self):
        g = self.game
        g.new_game("classic")
        for _ in range(400):
            if g.state == "quiz": self.answer_current(True)
            elif g.state != "play": break
            g.update(16)
            g.draw()

if __name__ == "__main__":
    unittest.main()
