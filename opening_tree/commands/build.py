from pathlib import Path
from ..repository.database import OpeningTreeRepository
from ..service.opening_tree import OpeningTreeService

def build_tree(args) -> None:
    """Build a new opening tree from a PGN file."""
    pgn_path = args.pgn_file
    db_path = args.db
    max_ply = args.max_ply
    min_rating = args.min_rating

    # If db_path is not provided, use the PGN path with .db extension
    if db_path is None:
        pgn_file = Path(pgn_path)
        if pgn_file.suffix.lower() == '.pgn':
            db_path = str(pgn_file.with_suffix('.db'))
        else:
            db_path = 'opening_tree.db'
    
    repository = OpeningTreeRepository(db_path)
    service = OpeningTreeService(repository, max_ply=max_ply, min_rating=min_rating)
    service.process_pgn_file(Path(pgn_path))