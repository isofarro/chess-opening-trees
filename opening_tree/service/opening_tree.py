from pathlib import Path
from typing import List, NamedTuple, Dict, Any
import chess
import hashlib
from datetime import datetime

from opening_tree.repository.database import OpeningTreeRepository
from opening_tree.parser.pgn_parser import PGNParser

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
    game_ref: str

class PGNFileMetadata(NamedTuple):
    filename: str
    name: str
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

        # Extract name from path (filename without extension)
        name = pgn_path.stem

        return PGNFileMetadata(
            filename=str(pgn_path),
            name=name,
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
        total_games = 0
        last_game = None
        for game in self.parser.parse_file(pgn_path):
            try:
                game_data = self._process_game(game, metadata.name)
                # Skip games where either player is below the minimum rating
                if (game_data.white_elo < self.min_rating or
                    game_data.black_elo < self.min_rating):
                    continue
                self.repository.add_game_to_opening_tree(game_data)
                games_processed = True
                total_games += 1
                last_game = game
            except Exception as e:
                print(f"Error processing game: {e}")

        # If at least one game was processed successfully, record the file import
        if games_processed:
            # Get the total number of games from the last game's GameNo header
            try:
                if last_game and 'GameNo' in last_game.headers:
                    total_games = int(last_game.headers['GameNo'])
            except (ValueError, TypeError):
                pass  # Keep the counted total if GameNo is invalid

            self.repository.add_imported_pgn_file(
                filename=metadata.filename,
                name=metadata.name,
                last_modified=metadata.last_modified,
                file_size=metadata.file_size,
                file_hash=metadata.file_hash,
                total_games=total_games
            )

    @staticmethod
    def _get_player_rating(game: chess.pgn.Game, color: str) -> int:
        """Extract player rating from game headers."""
        try:
            return int(game.headers.get(f'{color}Elo', '0'))
        except ValueError:
            return 0

    @staticmethod
    def _get_player_performance(game: chess.pgn.Game, color: str) -> int:
        """Calculate player performance from game headers and result.

        For each player, performance is calculated based on opponent's rating and game result:
        - Win: opponent's rating + 400 (with floor of player's own rating)
        - Draw: opponent's rating
        - Loss: opponent's rating - 400 (with ceiling of player's own rating)
        """
        try:
            result = game.headers.get('Result', '*')
            player_elo = int(game.headers.get(f'{color}Elo', '0'))
            opp_color = 'Black' if color == 'White' else 'White'
            opp_elo = int(game.headers.get(f'{opp_color}Elo', '0'))

            # Determine if the player won, lost, or drew
            if color == 'White':
                if result == '1-0':  # White win
                    return max(player_elo, opp_elo + 400)
                elif result == '0-1':  # White loss
                    return min(player_elo, opp_elo - 400)
                else:  # Draw
                    return opp_elo
            else:  # color == 'Black'
                if result == '0-1':  # Black win
                    return max(player_elo, opp_elo + 400)
                elif result == '1-0':  # Black loss
                    return min(player_elo, opp_elo - 400)
                else:  # Draw
                    return opp_elo
        except ValueError:
            return 0

    def _process_game(self, game: chess.pgn.Game, pgn_name: str = '') -> GameData:
        """Process a single game and return structured game data."""
        moves = []
        game_no = game.headers.get('GameNo', '0')
        game_ref = f"{pgn_name}:{game_no}"
        ply_count = 0

        # Extract player ratings and performance
        white_elo = self._get_player_rating(game, 'White')
        black_elo = self._get_player_rating(game, 'Black')
        white_performance = self._get_player_performance(game, 'White')
        black_performance = self._get_player_performance(game, 'Black')

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

        result = game.headers.get('Result', '*')
        game_date = self._format_pgn_date(game.headers.get('Date', ''))

        return GameData(
            moves=moves,
            result=result,
            white_elo=white_elo,
            black_elo=black_elo,
            date=game_date,
            white_performance=white_performance,
            black_performance=black_performance,
            game_ref=game_ref
        )

    @staticmethod
    def _format_pgn_date(pgn_date: str) -> str:
        """Convert PGN date format to ISO-8601.

        Handles formats:
        - YYYY.MM.DD -> YYYY-MM-DD
        - YYYY.MM.?? -> YYYY-MM
        - YYYY.??.?? -> YYYY
        - ????.??.?? -> ''
        """
        if not pgn_date or '????' in pgn_date:
            return ''

        parts = pgn_date.split('.')
        if len(parts) != 3:
            return ''

        # Convert valid parts to ISO format, stopping at first '??' encountered
        valid_parts = [p for p in parts if p != '??']
        if not valid_parts:
            return ''

        return '-'.join(valid_parts)

    @staticmethod
    def normalise_fen(fen: str) -> str:
        """Normalize a FEN string by keeping only the first 4 segments."""
        return ' '.join(fen.split()[:4])

    def query_position(self, fen: str) -> Dict[str, Any]:
        """Query a position and its possible moves with statistics.

        Args:
            fen: The FEN string to query (can be full or normalized)

        Returns:
            Dictionary containing the position FEN and list of possible moves with statistics
        """
        # Normalize FEN and get position data
        normalized_fen = self.normalise_fen(fen)
        position = self.repository.get_position_by_fen(normalized_fen)
        if not position:
            return None

        # Get raw moves data
        moves = self.repository.get_moves_from_position(position['id'])

        # Transform the moves data
        for move in moves:
            # Calculate average rating and performance
            move['rating'] = int(move['total_player_elo'] / move['total_games'])
            move['performance'] = int(move['total_player_performance'] / move['total_games'])

            # Remove raw data fields used for calculations
            del move['total_player_elo']
            del move['total_player_performance']

        return {
            "fen": position['fen'],
            "moves": moves
        }