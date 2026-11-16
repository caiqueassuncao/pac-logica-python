import os
import sys
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

APP_NAME = "PacLogica"
MAX_NAME = 14
DEFAULT_NAME = "Jogador"

@dataclass(frozen=True)
class Level:
    number: int
    goal: int
    dots: int
    ghosts: int
    ghost_step: int
    fruit_every: int
    topics: str = "conectivos"

    @property
    def topic_list(self):
        return tuple(t.strip() for t in self.topics.split(",") if t.strip())

SCHEMA_VERSION = 2

# Escala de níveis: (número, meta de pontos, docinhos, fantasmas,
# ms por passo do fantasma, ms entre frutas, tipos de questão)
DEFAULT_LEVELS = [
    (1, 6, 12, 2, 290, 14000, "conectivos"),
    (2, 8, 12, 2, 280, 13000, "conectivos"),
    (3, 9, 14, 2, 270, 12500, "conectivos,frases"),
    (4, 10, 14, 3, 260, 12000, "frases"),
    (5, 12, 16, 3, 245, 11000, "frases,argumentos"),
    (6, 13, 16, 3, 235, 10500, "argumentos"),
    (7, 15, 18, 4, 220, 10000, "conectivos,frases,argumentos"),
    (8, 18, 18, 4, 210, 9500, "conectivos,frases,argumentos,tabelas"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS levels (
    number      INTEGER PRIMARY KEY,
    goal        INTEGER NOT NULL,
    dots        INTEGER NOT NULL,
    ghosts      INTEGER NOT NULL,
    ghost_step  INTEGER NOT NULL,
    fruit_every INTEGER NOT NULL,
    topics      TEXT NOT NULL DEFAULT 'conectivos'
);
CREATE TABLE IF NOT EXISTS scores (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    player     TEXT NOT NULL,
    mode       TEXT NOT NULL CHECK (mode IN ('classic', 'arcade')),
    score      INTEGER NOT NULL,
    level      INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scores_mode_score ON scores (mode, score DESC);
CREATE TABLE IF NOT EXISTS players (
    name         TEXT PRIMARY KEY COLLATE NOCASE,
    best_level   INTEGER NOT NULL DEFAULT 0,
    games_played INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

def data_dir():
    """Pasta de dados do usuário conforme o sistema operacional."""
    override = os.environ.get("PACLOGICA_DATA_DIR")
    if override:
        base = Path(override)
    elif sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / APP_NAME
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / APP_NAME.lower()
    base.mkdir(parents=True, exist_ok=True)
    return base

def clean_name(name):
    name = " ".join(str(name).split())[:MAX_NAME]
    return name or DEFAULT_NAME

class Database:
    def __init__(self, path=None):
        if path is None:
            try:
                path = data_dir() / "paclogica.db"
            except OSError as exc:
                print(f"Aviso: sem acesso à pasta de dados ({exc}); o ranking não será salvo.")
                path = ":memory:"
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.executescript(SCHEMA)
            self.migrate()
            self.conn.executemany("INSERT OR IGNORE INTO levels VALUES (?,?,?,?,?,?,?)", DEFAULT_LEVELS)

    def migrate(self):
        version = int(self.get_setting("schema_version", "0"))
        if version < 2:
            # A versão 2 mudou a escala de pontos (docinho = 1 ponto) e os níveis ganharam
            # tipos de questão: recria os níveis e zera o ranking antigo, que não é comparável.
            self.conn.execute("DROP TABLE levels")
            self.conn.execute("DELETE FROM scores")
            self.conn.execute("UPDATE players SET best_level = 0")
            self.conn.executescript(SCHEMA)
        if version < SCHEMA_VERSION:
            self.set_setting("schema_version", SCHEMA_VERSION)

    def close(self):
        self.conn.close()

    # Níveis
    def levels(self):
        rows = self.conn.execute("SELECT * FROM levels ORDER BY number").fetchall()
        return [Level(**dict(r)) for r in rows]

    def level(self, number):
        row = self.conn.execute("SELECT * FROM levels WHERE number = ?", (number,)).fetchone()
        return Level(**dict(row)) if row else None

    def level_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM levels").fetchone()[0]

    # Ranking
    def save_score(self, player, mode, score, level):
        """Grava a partida e devolve (id, posição no ranking do modo)."""
        player = clean_name(player)
        now = datetime.now().isoformat(timespec="seconds")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO scores (player, mode, score, level, created_at) VALUES (?,?,?,?,?)",
                (player, mode, score, level, now))
            self.conn.execute(
                "INSERT INTO players (name, best_level, games_played) VALUES (?, ?, 1) "
                "ON CONFLICT(name) DO UPDATE SET games_played = games_played + 1, "
                "best_level = MAX(best_level, excluded.best_level)",
                (player, level if mode == "classic" else 0))
        return cur.lastrowid, self.rank_of(cur.lastrowid)

    def rank_of(self, score_id):
        row = self.conn.execute("SELECT mode, score FROM scores WHERE id = ?", (score_id,)).fetchone()
        if not row:
            return None
        ahead = self.conn.execute(
            "SELECT COUNT(*) FROM scores WHERE mode = ? AND (score > ? OR (score = ? AND id < ?))",
            (row["mode"], row["score"], row["score"], score_id)).fetchone()[0]
        return ahead + 1

    def top_scores(self, mode, limit=10):
        return self.conn.execute(
            "SELECT id, player, score, level, created_at FROM scores WHERE mode = ? "
            "ORDER BY score DESC, id ASC LIMIT ?", (mode, limit)).fetchall()

    def player_stats(self, player):
        player = clean_name(player)
        row = self.conn.execute(
            "SELECT best_level, games_played FROM players WHERE name = ?", (player,)).fetchone()
        best = {m: self.conn.execute(
                    "SELECT MAX(score) FROM scores WHERE mode = ? AND player = ? COLLATE NOCASE",
                    (m, player)).fetchone()[0] or 0
                for m in ("classic", "arcade")}
        return {
            "best_level": row["best_level"] if row else 0,
            "games": row["games_played"] if row else 0,
            "best_classic": best["classic"],
            "best_arcade": best["arcade"],
        }

    # Preferências
    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        with self.conn:
            self.conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
