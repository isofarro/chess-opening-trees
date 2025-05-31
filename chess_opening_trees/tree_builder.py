from pathlib import Path
from .repository.database import OpeningTreeRepository
from .service.opening_tree import OpeningTreeService

def process_pgn_file(pgn_path: str, db_path: str) -> None:
    """Process a PGN file and build/update the opening tree."""
    repository = OpeningTreeRepository(db_path)
    service = OpeningTreeService(repository)
    service.process_pgn_file(Path(pgn_path))

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Build a chess opening tree from PGN files")
    parser.add_argument("pgn_file", help="Path to the PGN file to process")
    parser.add_argument("--db", default="opening_tree.db", help="Path to the SQLite database file")
    
    args = parser.parse_args()
    process_pgn_file(args.pgn_file, args.db)

if __name__ == "__main__":
    main()
