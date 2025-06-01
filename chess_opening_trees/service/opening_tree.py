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
        game_data = {
            'result': game.headers.get('Result', '*'),
            'white_elo': int(game.headers.get('WhiteElo', '0')),
            'black_elo': int(game.headers.get('BlackElo', '0')),
            'date': game.headers.get('Date', '????-??-??')
        }
        
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
            self._update_position_stats(from_pos_id, game_data)
    
    def _update_position_stats(self, position_id: int, game_data: Dict[str, Any]) -> None:
        """Update statistics for a position based on game data."""
        # Initialize stats with default values if needed
        stats = {
            'total_games': 1,
            'white_wins': 1 if game_data['result'] == '1-0' else 0,
            'black_wins': 1 if game_data['result'] == '0-1' else 0,
            'draws': 1 if game_data['result'] == '1/2-1/2' else 0,
            'total_white_elo': game_data['white_elo'],
            'total_black_elo': game_data['black_elo'],
            'last_played_date': game_data['date']
        }
        
        self.repository.update_statistics(position_id, stats)