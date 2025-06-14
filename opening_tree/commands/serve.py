from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
import json
from typing import Dict

from opening_tree.repository.database import OpeningTreeRepository
from opening_tree.service.opening_tree import OpeningTreeService

class OpeningTreeHandler(BaseHTTPRequestHandler):
    def __init__(self, trees: Dict[str, OpeningTreeService], *args, **kwargs):
        self.trees = trees
        self.port = kwargs.pop('port', 2882)
        # Need to call parent's __init__ with original args
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Parse the URL path
        parsed_path = urlparse(self.path)
        path_segments = parsed_path.path.strip('/').split('/')

        # Handle root path - list available trees
        if not path_segments[0]:
            tree_list = [{
                'name': name,
                'path': f'http://localhost:{self.port}/{name}/{{fen}}'
            } for name in self.trees.keys()]

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(tree_list, indent=2).encode())
            return

        # Path should be /tree_name/fen
        if len(path_segments) != 2:
            self.send_error(400, "Invalid URL format. Expected: /tree_name/fen")
            return

        tree_name, encoded_fen = path_segments

        # Check if tree exists
        if tree_name not in self.trees:
            self.send_error(404, f"Tree '{tree_name}' not found")
            return

        # Decode FEN from URL
        fen = unquote(encoded_fen)

        # Query the position
        result = self.trees[tree_name].query_position(fen)
        if not result:
            self.send_error(404, f"Position not found: {fen}")
            return

        # Send successful response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result, indent=2).encode())

def create_handler(trees: Dict[str, OpeningTreeService], port: int):
    """Create a handler class with the tree services dictionary."""
    def handler(*args, **kwargs):
        return OpeningTreeHandler(trees, port=port, *args, **kwargs)
    return handler

def serve_tree(args) -> None:
    """Start an HTTP server to serve opening tree data."""
    # Create a dictionary of tree name to service
    trees = {}
    for name, db_path in args.trees:
        repository = OpeningTreeRepository(db_path)
        trees[name] = OpeningTreeService(repository)

    # Create and start the server
    port = args.port or 2882
    handler = create_handler(trees, port)
    server = HTTPServer(('localhost', port), handler)

    print(f"Starting server on port {port}")
    print("Available trees:")
    for name in trees.keys():
        print(f"  - {name}")
    print("\nEndpoints:")
    print(f"  GET http://localhost:{port}/          # List available trees")
    print(f"  GET http://localhost:{port}/tree_name/encoded_fen  # Query position")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server")
        server.server_close()