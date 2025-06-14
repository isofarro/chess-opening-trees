from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
import json
from typing import Dict

from opening_tree.repository.database import OpeningTreeRepository
from opening_tree.service.opening_tree import OpeningTreeService

class OpeningTreeHandler(BaseHTTPRequestHandler):
    def __init__(self, trees: Dict[str, OpeningTreeService], *args, **kwargs):
        self.trees = trees
        # Need to call parent's __init__ with original args
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Parse the URL path
        parsed_path = urlparse(self.path)
        path_segments = parsed_path.path.strip('/').split('/')
        
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

def create_handler(trees: Dict[str, OpeningTreeService]):
    """Create a handler class with the tree services dictionary."""
    def handler(*args, **kwargs):
        return OpeningTreeHandler(trees, *args, **kwargs)
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
    handler = create_handler(trees)
    server = HTTPServer(('localhost', port), handler)
    
    print(f"Starting server on port {port}")
    print("Available trees:")
    for name in trees.keys():
        print(f"  - {name}")
    print("\nExample URL format:")
    print(f"http://localhost:{port}/tree_name/encoded_fen")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server")
        server.server_close()