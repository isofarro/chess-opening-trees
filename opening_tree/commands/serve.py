from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import json
from typing import Dict

from opening_tree.service.api import OpeningTreeAPI, create_trees_from_config, load_config, get_trees_from_config

class OpeningTreeHandler(BaseHTTPRequestHandler):
    def __init__(self, api: OpeningTreeAPI, *args, **kwargs):
        self.api = api
        # Need to call parent's __init__ with original args
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Parse the URL path
        parsed_path = urlparse(self.path)
        path_segments = parsed_path.path.strip('/').split('/')

        # Route to appropriate handler
        if not path_segments[0]:
            self.handle_list_trees()
        elif len(path_segments) == 2:
            self.handle_query_position(path_segments[0], path_segments[1])
        else:
            self.send_error(400, "Invalid URL format. Expected: /tree_name/fen")

    def handle_list_trees(self):
        """Handle GET request for root path - list available trees."""
        tree_list = self.api.list_trees()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(tree_list, indent=2).encode())

    def handle_query_position(self, tree_name: str, encoded_fen: str):
        """Handle GET request for position query in a specific tree."""
        result, status_code, error_message = self.api.query_position(tree_name, encoded_fen)
        
        if status_code != 200:
            self.send_error(status_code, error_message)
            return

        # Send successful response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result, indent=2).encode())

def create_handler(api: OpeningTreeAPI):
    """Create a handler class with the API instance."""
    def handler(*args, **kwargs):
        return OpeningTreeHandler(api, *args, **kwargs)
    return handler

def serve_tree(args) -> None:
    """Start an HTTP server to serve opening tree data."""
    # Load configuration from file if provided
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # Determine port (command line takes precedence over config)
    port = args.port
    if port == 2882 and 'port' in config:  # Only use config port if default port is used
        port = config['port']
    
    # Determine trees (command line takes precedence over config)
    trees_list = []
    if args.trees:
        # Flatten the nested list from argparse
        for tree_pair in args.trees:
            if len(tree_pair) == 2:
                trees_list.append((tree_pair[0], tree_pair[1]))
            else:
                raise ValueError(f"Invalid tree specification: {tree_pair}. Expected name and path.")
    elif args.config:
        trees_list = get_trees_from_config(config)
    else:
        raise ValueError("No trees specified. Use --trees argument or provide trees in config file.")
    
    # Create trees from config or command line
    if args.config:
        trees = create_trees_from_config(args.config, trees_list)
    else:
        # For command line usage without config file
        from opening_tree.repository.database import OpeningTreeRepository
        from opening_tree.service.opening_tree import OpeningTreeService
        trees = {}
        for name, tree_path in trees_list:
            repository = OpeningTreeRepository(tree_path, read_only=True)
            trees[name] = OpeningTreeService(repository)

    # Create API instance with base URL
    protocol = 'http'  # Could be made configurable via args if needed
    domain = 'localhost'  # Could be made configurable via args if needed
    base_url = f"{protocol}://{domain}:{port}"
    api = OpeningTreeAPI(trees, base_url)
    
    # Create and start the server
    handler = create_handler(api)
    server = HTTPServer((domain, port), handler)

    print(f"Starting server on {protocol}://{domain}:{port}")
    if args.config:
        print(f"Using config file: {args.config}")
    print("Available trees:")
    for name in trees.keys():
        print(f"  - {name}")
    print("\nEndpoints:")
    print(f"  GET {protocol}://{domain}:{port}/          # List available trees")
    print(f"  GET {protocol}://{domain}:{port}/tree_name/encoded_fen  # Query position")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server")
        server.server_close()
