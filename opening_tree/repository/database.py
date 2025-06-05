from typing import Dict, Any
import sqlite3

class OpeningTreeRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
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
                    FOREIGN KEY (to_position_id) REFERENCES positions (id),
                    UNIQUE(from_position_id, to_position_id, move)
                );
                
                CREATE TABLE IF NOT EXISTS position_statistics (
                    position_id INTEGER PRIMARY KEY,
                    total_games INTEGER NOT NULL DEFAULT 0,
                    white_wins INTEGER NOT NULL DEFAULT 0,
                    black_wins INTEGER NOT NULL DEFAULT 0,
                    draws INTEGER NOT NULL DEFAULT 0,
                    total_white_elo INTEGER NOT NULL DEFAULT 0,
                    total_black_elo INTEGER NOT NULL DEFAULT 0,
                    last_played_date TEXT NOT NULL DEFAULT '',
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
            "INSERT OR IGNORE INTO moves (from_position_id, to_position_id, move) VALUES (?, ?, ?)",
            (from_pos_id, to_pos_id, move)
        )
    
    def update_statistics(self, position_id: int, new_stats: Dict[str, Any]) -> None:
        """Update statistics for a position, merging with existing stats if present."""
        self.conn.execute("""
            INSERT INTO position_statistics (
                position_id, total_games, white_wins, black_wins, draws,
                total_white_elo, total_black_elo, last_played_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(position_id) DO UPDATE SET
                total_games = total_games + excluded.total_games,
                white_wins = white_wins + excluded.white_wins,
                black_wins = black_wins + excluded.black_wins,
                draws = draws + excluded.draws,
                total_white_elo = total_white_elo + excluded.total_white_elo,
                total_black_elo = total_black_elo + excluded.total_black_elo,
                last_played_date = MAX(last_played_date, excluded.last_played_date)
        """, (
            position_id,
            new_stats['total_games'],
            new_stats['white_wins'],
            new_stats['black_wins'],
            new_stats['draws'],
            new_stats['total_white_elo'],
            new_stats['total_black_elo'],
            new_stats['last_played_date']
        ))
    
    def add_game_to_opening_tree(self, game_data: 'GameData') -> None:
        """Add a complete game to the opening tree within a single transaction."""
        self.start_game_transaction()
        try:
            # Process each move
            for move in game_data.moves:
                # Add positions
                from_pos_id = self.add_position(move.from_position)
                to_pos_id = self.add_position(move.to_position)
                
                # Add move
                self.add_move(from_pos_id, to_pos_id, move.move_san)
                
                # Update statistics for the starting position
                self._update_position_stats(from_pos_id, game_data)
            
            # Update statistics for the final position if there were any moves
            if game_data.moves:
                self._update_position_stats(to_pos_id, game_data)
                
            self.commit_game_transaction()
        except Exception as e:
            self.commit_game_transaction()  # or could add a rollback method
            raise e
    
    def _update_position_stats(self, position_id: int, game_data: 'GameData') -> None:
        """Update statistics for a position based on game data."""
        stats = {
            'total_games': 1,
            'white_wins': 1 if game_data.result == '1-0' else 0,
            'black_wins': 1 if game_data.result == '0-1' else 0,
            'draws': 1 if game_data.result == '1/2-1/2' else 0,
            'total_white_elo': game_data.white_elo,
            'total_black_elo': game_data.black_elo,
            'last_played_date': game_data.date
        }
        self.update_statistics(position_id, stats)