from pathlib import Path
from typing import List, NamedTuple
import chess

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

class OpeningTreeService:
    def __init__(self, repository: OpeningTreeRepository, max_moves: int = 40, min_rating: int = 0):
        self.repository = repository
        self.parser = PGNParser()
        self.max_moves = max_moves
        self.min_rating = min_rating
    
    def process_pgn_file(self, pgn_path: Path) -> None:
        """Process a PGN file and add its games to the opening tree."""
        for game in self.parser.parse_file(pgn_path):
            try:
                game_data = self._process_game(game)
                # Skip games where either player is below the minimum rating
                if (game_data.white_elo < self.min_rating or 
                    game_data.black_elo < self.min_rating):
                    continue
                self.repository.add_game_to_opening_tree(game_data)
            except Exception as e:
                print(f"Error processing game: {e}")

    def _process_game(self, game: chess.pgn.Game) -> GameData:
        """Process a single game and return structured game data."""
        moves = []
        move_count = 0
        
        for position_fen, move_san in self.parser.extract_moves(game):
            if move_count >= self.max_moves:
                break
                
            # Normalize FEN by keeping only the first 4 segments
            from_position = self.normalise_fen(position_fen)
            
            # Create the next position to get its FEN
            board = chess.Board(position_fen)
            move = board.parse_san(move_san)
            board.push(move)
            to_position = self.normalise_fen(board.fen())
            
            moves.append(GameMove(from_position, to_position, move_san))
            move_count += 1
        
        return GameData(
            moves=moves,
            result=game.headers.get('Result', '*'),
            white_elo=int(game.headers.get('WhiteElo', '0')),
            black_elo=int(game.headers.get('BlackElo', '0')),
            date=game.headers.get('Date', '????-??-??')
        )
    
    @staticmethod
    def normalise_fen(fen: str) -> str:
        """Normalize a FEN string by keeping only the first 4 segments."""
        return ' '.join(fen.split()[:4])