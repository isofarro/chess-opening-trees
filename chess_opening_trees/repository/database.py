from typing import Dict, Any
import sqlite3
import json

class OpeningTreeRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
        self.conn = None
    
    def _init_database(self) -> None:
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    fen TEXT UNIQUE NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS moves (
                    id INTEGER PRIMARY KEY,
                    from_position_id INTEGER NOT NULL,
                    to_position_id INTEGER NOT NULL,
                    move TEXT NOT NULL,
                    FOREIGN KEY (from_position_id) REFERENCES positions (id),
                    FOREIGN KEY (to_position_id) REFERENCES positions (id)
                );
                
                CREATE TABLE IF NOT EXISTS position_statistics (
                    position_id INTEGER PRIMARY KEY,
                    statistics TEXT NOT NULL,  -- JSON object
                    FOREIGN KEY (position_id) REFERENCES positions (id)
                );
            """)
    
    def start_game_transaction(self):
        """Start a new transaction for processing a game."""
        if self.conn is not None:
            self.conn.close()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("BEGIN TRANSACTION")
    
    def commit_game_transaction(self):
        """Commit the current game transaction."""
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None
    
    def add_position(self, fen: str) -> int:
        """Add a position to the database and return its ID."""
        cursor = self.conn.execute(
            "INSERT OR IGNORE INTO positions (fen) VALUES (?)",
            (fen,)
        )
        if cursor.rowcount == 0:  # Position already exists
            return self.conn.execute(
                "SELECT id FROM positions WHERE fen = ?",
                (fen,)
            ).fetchone()[0]
        return cursor.lastrowid
    
    def add_move(self, from_pos_id: int, to_pos_id: int, move: str) -> None:
        """Add a move between two positions."""
        self.conn.execute(
            "INSERT INTO moves (from_position_id, to_position_id, move) VALUES (?, ?, ?)",
            (from_pos_id, to_pos_id, move)
        )
    
    def update_statistics(self, position_id: int, stats: Dict[str, Any]) -> None:
        """Update statistics for a position."""
        self.conn.execute(
            "INSERT OR REPLACE INTO position_statistics (position_id, statistics) VALUES (?, ?)",
            (position_id, json.dumps(stats))
        )