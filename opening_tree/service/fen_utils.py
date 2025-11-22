import re

def _expand_fen_rank(rank_str: str) -> str:
    joined = ''.join((' ' * int(ch)) if ch.isdigit() else ch for ch in rank_str)
    return (joined + ' ' * 8)[:8]

def _normalise_en_passant(ep: str, piece_placement: str, active_color: str) -> str:
    if ep == '-':
        return ep
    if not re.match(r'^[a-h][36]$', ep):
        return ep
    file_idx = ord(ep[0]) - 97
    is_white_to_move = active_color == 'w'
    pawn_char = 'P' if is_white_to_move else 'p'
    pawn_rank_idx = 8 - (5 if is_white_to_move else 4)
    ranks = piece_placement.split('/')
    rank_expanded = _expand_fen_rank(ranks[pawn_rank_idx])
    left_ok = (file_idx - 1) >= 0 and rank_expanded[file_idx - 1] == pawn_char
    right_ok = (file_idx + 1) <= 7 and rank_expanded[file_idx + 1] == pawn_char
    return ep if (left_ok or right_ok) else '-'

def is_legal_enpassant(fen: str) -> bool:
    parts = [p for p in fen.strip().split() if p]
    if len(parts) < 4:
        return False
    ep = parts[3]
    if ep == '-':
        return False
    return _normalise_en_passant(ep, parts[0], parts[1]) == ep

def normalise_fen(fen: str) -> str:
    parts = [p for p in fen.strip().split() if p]
    if len(parts) < 4:
        raise ValueError(f"Invalid FEN string: insufficient parts - {fen}")
    piece_placement, active_color, castling_rights, en_passant_target = parts[:4]
    ep = _normalise_en_passant(en_passant_target, piece_placement, active_color)
    return f"{piece_placement} {active_color} {castling_rights} {ep}"
