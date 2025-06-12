import argparse
from opening_tree.commands.build import build_tree
from opening_tree.commands.prune import prune_tree
from opening_tree.commands.query import query_tree

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
        "pgn_files",
        nargs="+",
        help="One or more PGN files to process (glob patterns are supported, e.g., *.pgn)"
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

    # Prune command
    prune_parser = subparsers.add_parser(
        "prune",
        help="Prune single-game positions from the opening tree"
    )
    prune_parser.add_argument(
        "db",
        help="Path to the SQLite database file to prune"
    )
    prune_parser.add_argument(
        "--max-closeness",
        type=int,
        default=5,
        help="Maximum closeness score for keeping single-game positions (default: 5)"
    )
    prune_parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of positions to process in each batch (default: 1000)"
    )

    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query the opening tree for a specific position"
    )
    query_parser.add_argument(
        "db",
        help="Path to the SQLite database file to query"
    )
    query_parser.add_argument(
        "--fen",
        required=True,
        help="FEN string of the position to query"
    )
    query_parser.add_argument(
        "--output",
        default="json",
        choices=["json"],
        help="Output format (default: json)"
    )

    args = parser.parse_args()

    if args.command == "build":
        build_tree(args)
    elif args.command == "prune":
        prune_tree(args)
    elif args.command == "query":
        query_tree(args)
    elif not args.command:
        parser.print_help()

if __name__ == "__main__":
    main()