from typing import Dict, Any
import sqlite3

class OpeningTreeRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database with required tables."""
        self.conn.executescript("""
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

            CREATE TABLE IF NOT EXISTS imported_pgn_files (
                id INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                last_modified TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT NOT NULL,
                import_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filename, file_hash)
            );
        """)

    def start_game_transaction(self):
        """Start a new transaction for processing a game."""
        self.conn.execute("BEGIN TRANSACTION")

    def commit_game_transaction(self):
        """Commit the current game transaction."""
        self.conn.commit()

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

    def add_imported_pgn_file(self, filename: str, last_modified: str, file_size: int, file_hash: str) -> None:
        """Record a successfully imported PGN file."""
        self.conn.execute("BEGIN TRANSACTION")
        try:
            self.conn.execute("""
                INSERT INTO imported_pgn_files (filename, last_modified, file_size, file_hash)
                VALUES (?, ?, ?, ?)
            """, (filename, last_modified, file_size, file_hash))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_imported_pgn_file(self, filename: str, file_hash: str) -> Dict[str, Any] | None:
        """Check if a PGN file has already been imported.

        Returns the import record if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT filename, last_modified, file_size, file_hash, import_date FROM imported_pgn_files WHERE filename = ? AND file_hash = ?",
            (filename, file_hash)
        )
        row = cursor.fetchone()
        if row:
            return {
                'filename': row[0],
                'last_modified': row[1],
                'file_size': row[2],
                'file_hash': row[3],
                'import_date': row[4]
            }
        return None
