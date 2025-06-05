from pathlib import Path
import argparse
from .commands.build import build_tree

def main():
    parser = argparse.ArgumentParser(
        description="Chess opening tree analysis tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Build command
    build_parser = subparsers.add_parser(
        "build", 
        help="Build a new opening tree from PGN files"
    )
    build_parser.add_argument(
        "pgn_file",
        help="Path to the PGN file to process"
    )
    build_parser.add_argument(
        "--db",
        default=None,
        help="Path to the SQLite database file (default: same as PGN file with .db extension)"
    )
    build_parser.add_argument(
        "--max-ply",
        type=int,
        default=30,
        help="Maximum number of half-moves (ply) to process per game (default: 30)"
    )
    build_parser.add_argument(
        "--min-rating",
        type=int,
        default=0,
        help="Minimum rating required for both players (default: 0)"
    )

    args = parser.parse_args()
    
    if args.command == "build":
        build_tree(args)
    elif not args.command:
        parser.print_help()

if __name__ == "__main__":
    main()