from pathlib import Path
from typing import Dict, Any
import chess

from ..repository.database import OpeningTreeRepository
from ..parser.pgn_parser import PGNParser

class OpeningTreeService:
    def __init__(self, repository: OpeningTreeRepository):
        self.repository = repository
        self.parser = PGNParser()
    
    def process_pgn_file(self, pgn_path: Path) -> None:
        """Process a PGN file and add its games to the opening tree."""
        for game in self.parser.parse_file(pgn_path):
            self.repository.start_game_transaction()
            try:
                self._process_game(game)
                self.repository.commit_game_transaction()
            except Exception as e:
                print(f"Error processing game: {e}")
                self.repository.commit_game_transaction()  # or could add a rollback method
    
    def _process_game(self, game: chess.pgn.Game) -> None:
        """Process a single game and update the opening tree."""
        result = self._get_game_result(game)
        
        for position_fen, move_san in self.parser.extract_moves(game):
            # Add positions and moves to the database
            from_pos_id = self.repository.add_position(position_fen)
            
            # Create the next position to get its FEN
            board = chess.Board(position_fen)
            move = board.parse_san(move_san)
            board.push(move)
            to_pos_fen = board.fen()
            
            to_pos_id = self.repository.add_position(to_pos_fen)
            self.repository.add_move(from_pos_id, to_pos_id, move_san)
            
            # Update statistics
            self._update_position_stats(from_pos_id, result)
    
    def _get_game_result(self, game: chess.pgn.Game) -> str:
        """Extract the game result: '1-0', '0-1', or '1/2-1/2'."""
        return game.headers.get("Result", "*")
    
    def _update_position_stats(self, position_id: int, result: str) -> None:
        """Update statistics for a position based on game result."""
        # Initialize stats with default values if needed
        stats: Dict[str, Any] = {
            "total_games": 1,
            "white_wins": 1 if result == "1-0" else 0,
            "black_wins": 1 if result == "0-1" else 0,
            "draws": 1 if result == "1/2-1/2" else 0
        }
        
        self.repository.update_statistics(position_id, stats)