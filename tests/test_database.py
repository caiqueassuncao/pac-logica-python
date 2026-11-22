import unittest
from paclogica.database import Database, DEFAULT_LEVELS

class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_levels_are_seeded(self):
        self.assertEqual(self.db.level_count(), len(DEFAULT_LEVELS))
        self.assertEqual(self.db.level(1).goal, DEFAULT_LEVELS[0][1])
        self.assertIsNone(self.db.level(999))

    def test_ranking_order_and_position(self):
        self.db.save_score("Ana", "arcade", 500, 2)
        _, rank = self.db.save_score("Bia", "arcade", 900, 3)
        self.assertEqual(rank, 1)
        _, rank = self.db.save_score("Caio", "arcade", 500, 1)
        self.assertEqual(rank, 3)
        self.db.save_score("Ana", "classic", 2000, 4)
        top = self.db.top_scores("arcade")
        self.assertEqual([r["player"] for r in top], ["Bia", "Ana", "Caio"])

    def test_player_stats(self):
        self.db.save_score("Ana", "classic", 800, 3)
        self.db.save_score("ana", "classic", 300, 2)
        self.db.save_score("Ana", "arcade", 1200, 4)
        stats = self.db.player_stats("Ana")
        self.assertEqual(stats["best_level"], 3)
        self.assertEqual(stats["games"], 3)
        self.assertEqual(stats["best_classic"], 800)
        self.assertEqual(stats["best_arcade"], 1200)

    def test_blank_name_gets_default(self):
        self.db.save_score("   ", "arcade", 10, 1)
        self.assertEqual(self.db.top_scores("arcade")[0]["player"], "Jogador")

    def test_migrates_version_1_database(self):
        import os, sqlite3, tempfile
        path = os.path.join(tempfile.mkdtemp(), "v1.db")
        old = sqlite3.connect(path)
        old.executescript("""
            CREATE TABLE levels (number INTEGER PRIMARY KEY, goal INTEGER, dots INTEGER,
                                 ghosts INTEGER, ghost_step INTEGER, fruit_every INTEGER);
            INSERT INTO levels VALUES (1, 400, 12, 2, 285, 14000);
            CREATE TABLE scores (id INTEGER PRIMARY KEY AUTOINCREMENT, player TEXT NOT NULL,
                mode TEXT NOT NULL, score INTEGER NOT NULL, level INTEGER NOT NULL, created_at TEXT NOT NULL);
            INSERT INTO scores (player, mode, score, level, created_at) VALUES ('Ana', 'arcade', 2350, 4, '2026-11-16');
        """)
        old.commit(); old.close()
        db = Database(path)
        self.assertEqual(db.level(1).goal, DEFAULT_LEVELS[0][1])
        self.assertEqual(db.level(3).topic_list, ("conectivos", "frases"))
        self.assertEqual(db.top_scores("arcade"), [])
        db.save_score("Ana", "arcade", 5, 1)
        db.close()
        db = Database(path)  # reabrir não migra de novo
        self.assertEqual(len(db.top_scores("arcade")), 1)
        db.close()

    def test_settings(self):
        self.assertEqual(self.db.get_setting("x", "padrão"), "padrão")
        self.db.set_setting("x", "1")
        self.db.set_setting("x", "2")
        self.assertEqual(self.db.get_setting("x"), "2")

if __name__ == "__main__":
    unittest.main()
