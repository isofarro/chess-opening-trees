from pathlib import Path
from typing import List, NamedTuple
import chess
import hashlib
from datetime import datetime

from ..repository.database import OpeningTreeRepository
from ..parser.pgn_parser import PGNParser

class GameMove(NamedTuple):
    from_position: str  # FEN
    to_position: str    # FEN
    move_san: str

class GameData(NamedTuple):
    moves: List[GameMove]
    result: str
    white_elo: int
    black_elo: int
    date: str
    white_performance: int
    black_performance: int

class PGNFileMetadata(NamedTuple):
    filename: str
    last_modified: str
    file_size: int
    file_hash: str

class OpeningTreeService:
    def __init__(self, repository: OpeningTreeRepository, max_ply: int = 40, min_rating: int = 0):
        self.repository = repository
        self.parser = PGNParser()
        self.max_ply = max_ply
        self.min_rating = min_rating

    def _get_pgn_file_metadata(self, pgn_path: Path) -> PGNFileMetadata:
        """Get metadata for a PGN file including size, modification time, and hash."""
        # Get file information
        file_stats = pgn_path.stat()
        file_size = file_stats.st_size
        last_modified = file_stats.st_mtime_ns

        # Calculate file hash
        sha256_hash = hashlib.sha256()
        with open(pgn_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        file_hash = sha256_hash.hexdigest()

        # Convert timestamp to ISO format
        last_modified_date = datetime.fromtimestamp(last_modified / 1e9).isoformat()

        return PGNFileMetadata(
            filename=str(pgn_path),
            last_modified=last_modified_date,
            file_size=file_size,
            file_hash=file_hash
        )

    def process_pgn_file(self, pgn_path: Path) -> None:
        """Process a PGN file and add its games to the opening tree."""
        # Get file metadata before processing
        metadata = self._get_pgn_file_metadata(pgn_path)

        # Check if this exact file has already been imported
        existing = self.repository.get_imported_pgn_file(metadata.filename, metadata.file_hash)
        if existing:
            print(f"Skipping {metadata.filename} - already imported on {existing['import_date']}")
            return

        # Process all games in the file
        games_processed = False
        for game in self.parser.parse_file(pgn_path):
            try:
                game_data = self._process_game(game)
                # Skip games where either player is below the minimum rating
                if (game_data.white_elo < self.min_rating or
                    game_data.black_elo < self.min_rating):
                    continue
                self.repository.add_game_to_opening_tree(game_data)
                games_processed = True
            except Exception as e:
                print(f"Error processing game: {e}")

        # If at least one game was processed successfully, record the file import
        if games_processed:
            self.repository.add_imported_pgn_file(
                filename=metadata.filename,
                last_modified=metadata.last_modified,
                file_size=metadata.file_size,
                file_hash=metadata.file_hash
            )

    def _process_game(self, game: chess.pgn.Game) -> GameData:
        """Process a single game and return structured game data."""
        moves = []
        ply_count = 0

        for position_fen, move_san in self.parser.extract_moves(game):
            if ply_count >= self.max_ply:
                break

            # Normalize FEN by keeping only the first 4 segments
            from_position = self.normalise_fen(position_fen)

            # Create the next position to get its FEN
            board = chess.Board(position_fen)
            move = board.parse_san(move_san)
            board.push(move)
            to_position = self.normalise_fen(board.fen())

            moves.append(GameMove(from_position, to_position, move_san))
            ply_count += 1

        white_elo = int(game.headers.get('WhiteElo', '0'))
        black_elo = int(game.headers.get('BlackElo', '0'))
        result = game.headers.get('Result', '*')

        # Calculate performance ratings
        if result == '1-0':  # White win
            white_performance = max(white_elo, black_elo + 400)
            black_performance = min(black_elo, white_elo - 400)
        elif result == '0-1':  # Black win
            white_performance = min(white_elo, black_elo - 400)
            black_performance = max(black_elo, white_elo + 400)
        else:  # Draw or unknown result
            white_performance = black_elo
            black_performance = white_elo

        game_date = game.headers.get('Date', '')
        if game_date == '????.??.??':
            game_date = ''

        return GameData(
            moves=moves,
            result=result,
            white_elo=white_elo,
            black_elo=black_elo,
            date=game_date,
            white_performance=white_performance,
            black_performance=black_performance
        )

    @staticmethod
    def normalise_fen(fen: str) -> str:
        """Normalize a FEN string by keeping only the first 4 segments."""
        return ' '.join(fen.split()[:4])