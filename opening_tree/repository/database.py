from typing import Dict, Any, List
import sqlite3

class OpeningTreeRepository:
    def __init__(self, tree_path: str):
        self.tree_path = tree_path
        self.conn = sqlite3.connect(tree_path)
        self._configure_sqlite_performance()
        self._init_database()
    
    def _configure_sqlite_performance(self) -> None:
        """Configure SQLite for optimal performance."""
        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        
        # Increase cache size (default is 2MB, set to 64MB)
        self.conn.execute("PRAGMA cache_size=-65536")
        
        # Use memory for temporary tables
        self.conn.execute("PRAGMA temp_store=MEMORY")
        
        # Optimize synchronization for better performance
        self.conn.execute("PRAGMA synchronous=NORMAL")
        
        # Set busy timeout to handle concurrent access
        self.conn.execute("PRAGMA busy_timeout=30000")
        
        # Enable query planner optimizations
        self.conn.execute("PRAGMA optimize")
        
        # Commit the PRAGMA settings
        self.conn.commit()

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
                total_player_elo INTEGER NOT NULL DEFAULT 0,
                total_player_performance INTEGER NOT NULL DEFAULT 0,
                last_played_date TEXT NOT NULL DEFAULT '',
                game_ref TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (position_id) REFERENCES positions (id)
            );

            CREATE TABLE IF NOT EXISTS imported_pgn_files (
                id INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                name TEXT NOT NULL,
                last_modified TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT NOT NULL,
                total_games INTEGER NOT NULL DEFAULT 0,
                import_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filename, file_hash)
            );

            -- Performance indexes for large databases
            CREATE INDEX IF NOT EXISTS idx_moves_from_position ON moves(from_position_id);

            -- Analyze tables for query optimization
            ANALYZE;
        """)

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
                total_player_elo, total_player_performance, last_played_date, game_ref
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(position_id) DO UPDATE SET
                total_games = total_games + excluded.total_games,
                white_wins = white_wins + excluded.white_wins,
                black_wins = black_wins + excluded.black_wins,
                draws = draws + excluded.draws,
                total_player_elo = total_player_elo + excluded.total_player_elo,
                total_player_performance = total_player_performance + excluded.total_player_performance,
                last_played_date = MAX(last_played_date, excluded.last_played_date),
                game_ref = CASE
                    WHEN excluded.last_played_date > last_played_date THEN excluded.game_ref
                    ELSE game_ref
                END
        """, (
            position_id,
            new_stats['total_games'],
            new_stats['white_wins'],
            new_stats['black_wins'],
            new_stats['draws'],
            new_stats['total_player_elo'],
            new_stats['total_player_performance'],
            new_stats['last_played_date'],
            new_stats['game_ref']
        ))

    def _update_position_stats(self, position_id: int, game_data: 'GameData', is_white_to_move: bool) -> None:
        """Update statistics for a position based on game data."""
        # If white is to move, black just moved, and vice versa
        just_moved_is_white = not is_white_to_move

        # Get the appropriate ratings based on who just moved
        if just_moved_is_white:
            player_elo = game_data.white_elo
            player_performance = game_data.white_performance
        else:
            player_elo = game_data.black_elo
            player_performance = game_data.black_performance

        stats = {
            'total_games': 1,
            'white_wins': 1 if game_data.result == '1-0' else 0,
            'black_wins': 1 if game_data.result == '0-1' else 0,
            'draws': 1 if game_data.result == '1/2-1/2' else 0,
            'total_player_elo': player_elo,
            'total_player_performance': player_performance,
            'last_played_date': game_data.date,
            'game_ref': game_data.game_ref
        }
        self.update_statistics(position_id, stats)

    def add_game_to_opening_tree(self, game_data: 'GameData') -> None:
        """Add a complete game to the opening tree within a single transaction."""
        self.conn.execute("BEGIN TRANSACTION")
        try:
            # Process each move
            for move in game_data.moves:
                # Add positions
                from_pos_id = self.add_position(move.from_position)
                to_pos_id = self.add_position(move.to_position)

                # Add move
                self.add_move(from_pos_id, to_pos_id, move.move_san)

                # Get who is to move from the FEN (2nd segment)
                is_white_to_move = move.from_position.split()[1] == 'w'

                # Update statistics for the starting position
                self._update_position_stats(from_pos_id, game_data, is_white_to_move)

            # Update statistics for the final position if there were any moves
            if game_data.moves:
                is_white_to_move = move.to_position.split()[1] == 'w'
                self._update_position_stats(to_pos_id, game_data, is_white_to_move)

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_imported_pgn_file(self, filename: str, name: str, last_modified: str, file_size: int, file_hash: str, total_games: int) -> None:
        """Record a successfully imported PGN file."""
        self.conn.execute("BEGIN TRANSACTION")
        try:
            self.conn.execute("""
                INSERT INTO imported_pgn_files (filename, name, last_modified, file_size, file_hash, total_games)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (filename, name, last_modified, file_size, file_hash, total_games))
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

    def get_position_by_fen(self, fen: str) -> Dict[str, Any] | None:
        """Get a position by its FEN string.

        Args:
            fen: The normalized FEN string to look up (first 4 segments only).

        Returns:
            Position data if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT id, fen FROM positions WHERE fen = ?", (fen,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'fen': row[1]
            }
        return None

    def get_moves_from_position(self, position_id: int) -> List[Dict[str, Any]]:
        """Get all moves and their statistics from a given position.

        Args:
            position_id: ID of the position to get moves from.

        Returns:
            List of moves with their statistics.
        """
        cursor = self.conn.execute("""
            SELECT
                m.move,
                p.fen,
                s.total_games,
                s.white_wins,
                s.draws,
                s.black_wins,
                s.total_player_elo,
                s.total_player_performance,
                s.last_played_date,
                s.game_ref
            FROM moves m
            JOIN positions p ON m.to_position_id = p.id
            JOIN position_statistics s ON m.to_position_id = s.position_id
            WHERE m.from_position_id = ?
            ORDER BY s.total_games DESC
        """, (position_id,))

        return [{
            "move": row[0],
            "fen": row[1],
            "total_games": row[2],
            "white_wins": row[3],
            "draws": row[4],
            "black_wins": row[5],
            "total_player_elo": row[6],
            "total_player_performance": row[7],
            "last_played_date": row[8],
            "game_ref": row[9]
        } for row in cursor.fetchall()]
