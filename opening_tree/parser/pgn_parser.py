from typing import Iterator, Tuple, Optional
import chess.pgn
from pathlib import Path
from datetime import datetime

class PGNParser:
    @staticmethod
    def parse_file(pgn_path: Path) -> Iterator[chess.pgn.Game]:
        """Parse a PGN file and yield each game.

        Skips games that use chess variants (e.g., Chess960) by checking the 'Variant' header.
        Only standard chess games are processed.
        """
        game_count = 0
        with open(pgn_path, encoding='iso-8859-1') as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break

                # Skip games that use chess variants
                if 'Variant' in game.headers:
                    continue

                game_count += 1
                print(f"Game: {game_count}", end='\r')
                yield game

    @staticmethod
    def extract_moves(game: chess.pgn.Game) -> Iterator[Tuple[str, str]]:
        """Extract moves from a game, yielding (position_fen, move_san) pairs."""
        board = game.board()
        for move in game.mainline_moves():
            position_fen = board.fen()
            move_san = board.san(move)
            board.push(move)
            yield position_fen, move_san