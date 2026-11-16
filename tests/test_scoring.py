import unittest
from paclogica.config import CANDY_POINTS
from paclogica.scoring import Scoreboard, FRUITS

FRUIT = {f.key: f for f in FRUITS}

class ScoreboardTest(unittest.TestCase):
    def test_correct_answer_is_worth_one_candy(self):
        s = Scoreboard()
        self.assertEqual(s.correct_answer(), CANDY_POINTS)
        self.assertEqual(s.correct_answer(), CANDY_POINTS)
        self.assertEqual(s.streak, 2)
        s.wrong_answer()
        self.assertEqual(s.streak, 0)

    def test_bonus_fruit_adds_points(self):
        s = Scoreboard()
        self.assertEqual(s.eat_fruit(FRUIT["morango"]), 3)
        self.assertEqual((s.score, s.level_score), (3, 3))

    def test_fruits_are_worth_more_than_candy(self):
        for f in FRUITS:
            self.assertTrue(f.bonus > CANDY_POINTS or f.multiplier > 1, f.key)

    def test_multiplier_applies_and_expires(self):
        s = Scoreboard()
        s.eat_fruit(FRUIT["laranja"])
        self.assertEqual(s.correct_answer(), 2)
        s.tick(FRUIT["laranja"].duration)
        self.assertEqual(s.multiplier, 1)
        self.assertEqual(s.correct_answer(), 1)

    def test_lower_multiplier_does_not_replace_higher(self):
        s = Scoreboard()
        s.eat_fruit(FRUIT["uva"])
        s.tick(5000)
        s.eat_fruit(FRUIT["laranja"])
        self.assertEqual(s.multiplier, 3)
        self.assertLessEqual(s.mult_left, s.mult_total)

    def test_new_level_keeps_total(self):
        s = Scoreboard()
        s.add(5)
        s.new_level()
        self.assertEqual((s.score, s.level_score), (5, 0))

if __name__ == "__main__":
    unittest.main()
