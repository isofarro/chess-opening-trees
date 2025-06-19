import argparse
from opening_tree.commands.build import build_tree
from opening_tree.commands.prune import prune_tree
from opening_tree.commands.query import query_tree
from opening_tree.commands.serve import serve_tree

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
        "--tree",
        dest="tree",
        default=None,
        help="Path to the opening tree file (default: same as PGN file with .tree extension)"
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
        "tree",
        help="The tree file to prune"
    )
    prune_parser.add_argument(
        "--workspace",
        help="Path to the workspace tree file (default: in-memory database)"
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
        default=5000,
        help="Number of positions to process in each batch (default: 5000)"
    )

    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query the opening tree for a specific position"
    )
    query_parser.add_argument(
        "tree",
        help="The tree file to query"
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

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start an HTTP server to serve opening tree data"
    )
    serve_parser.add_argument(
        "--trees",
        nargs="+",
        action="append",
        required=True,
        metavar=("NAME", "TREE"),
        help="Tree name and file pairs (e.g., --trees main main.tree --trees test test.tree)"
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=2882,
        help="Port to run the server on (default: 2882)"
    )

    args = parser.parse_args()

    if args.command == "build":
        build_tree(args)
    elif args.command == "prune":
        prune_tree(args)
    elif args.command == "query":
        query_tree(args)
    elif args.command == "serve":
        serve_tree(args)
    elif not args.command:
        parser.print_help()

if __name__ == "__main__":
    main()