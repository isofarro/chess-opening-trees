from pathlib import Path
from itertools import chain
from opening_tree.repository.database import OpeningTreeRepository
from opening_tree.service.opening_tree import OpeningTreeService

def find_pgn_files(path: Path) -> list[Path]:
    """Find all PGN files in a path, handling files, directories, and glob patterns."""
    if '*' in str(path) or '?' in str(path):
        return list(Path().glob(str(path)))

    path = Path(path)
    if not path.exists():
        print(f"Warning: {path} does not exist, skipping")
        return []

    if path.is_file():
        return [path] if path.suffix.lower() == '.pgn' else []

    if path.is_dir():
        return list(path.glob('**/*.pgn'))

    return []

def build_tree(args) -> None:
    """Build a new opening tree from PGN files."""
    # Collect all PGN files from arguments
    pgn_paths = []
    for pattern in args.pgn_files:
        found_files = find_pgn_files(Path(pattern))
        if found_files:
            pgn_paths.extend(found_files)
        else:
            print(f"Warning: No PGN files found for {pattern}")

    # Verify we found at least one PGN file
    if not pgn_paths:
        print("Error: No PGN files found matching the specified patterns")
        return

    # If tree_path is not provided, use the first PGN path with .tree extension
    tree_path = args.tree
    if tree_path is None:
        first_pgn = pgn_paths[0]
        if first_pgn.suffix.lower() == '.pgn':
            tree_path = str(first_pgn.with_suffix('.tree'))
        else:
            tree_path = 'opening_tree.tree'

    repository = OpeningTreeRepository(tree_path)
    service = OpeningTreeService(repository, max_ply=args.max_ply, min_rating=args.min_rating)

    # Process each PGN file
    total_files = len(pgn_paths)
    for idx, pgn_path in enumerate(pgn_paths, 1):
        print(f"Processing {pgn_path} ({idx}/{total_files})...")
        service.process_pgn_file(pgn_path)