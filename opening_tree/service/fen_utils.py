def is_legal_enpassant(fen: str) -> bool:
    """Check if en-passant is legal in a given FEN position."""
    fen_parts = fen.split()[:4]
    ep_square = fen_parts[3]

    if ep_square == '-':
        return False

    is_white_to_move = fen_parts[1] = 'w'
    pawn = ('P' if is_white_to_move else 'p')
    ep_file_idx = ord(ep_square[0]) - ord('a')
    pawn_rank_no = (5 if is_white_to_move else 4)

    rank_rle = fen_parts[0].split('/')[8 - pawn_rank_no]
    rank = ''.join(
        [' ' * int(c) if c.isdigit() else c for c in rank_rle]
    )

    if ep_file_idx > 0 and rank[ep_file_idx - 1] == pawn:
        return True
    elif ep_file_idx < 7 and rank[ep_file_idx + 1] == pawn:
        return True

    # No legal en-passant move found
    return False

def normalise_fen(fen: str) -> str:
    """Normalize a FEN string by keeping only the first 4 segments."""
    fen_parts = fen.split()[:4]

    # Legal en-passant check
    fen_parts[3] = (fen_parts[3] if is_legal_enpassant(fen) else '-')

    return ' '.join(fen_parts)
