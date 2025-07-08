from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
import json
from typing import Dict, List, Tuple
from pathlib import Path

from opening_tree.repository.database import OpeningTreeRepository
from opening_tree.service.opening_tree import OpeningTreeService

class OpeningTreeHandler(BaseHTTPRequestHandler):
    def __init__(self, trees: Dict[str, OpeningTreeService], *args, **kwargs):
        self.trees = trees
        self.port = kwargs.pop('port', 2882)
        self.protocol = kwargs.pop('protocol', 'http')
        self.domain = kwargs.pop('domain', 'localhost')
        # Need to call parent's __init__ with original args
        super().__init__(*args, **kwargs)

    @property
    def base_url(self) -> str:
        """Get the base URL for the server."""
        return f"{self.protocol}://{self.domain}:{self.port}"

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
        tree_list = [{
            'name': name,
            'path': f'{self.base_url}/{name}/{{fen}}'
        } for name in self.trees.keys()]

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(tree_list, indent=2).encode())

    def handle_query_position(self, tree_name: str, encoded_fen: str):
        """Handle GET request for position query in a specific tree."""
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

def create_handler(trees: Dict[str, OpeningTreeService], port: int, protocol: str = 'http', domain: str = 'localhost'):
    """Create a handler class with the tree services dictionary."""
    def handler(*args, **kwargs):
        return OpeningTreeHandler(trees, port=port, protocol=protocol, domain=domain, *args, **kwargs)
    return handler

def load_config(config_path: str) -> Dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_path}: {e}")

def get_trees_from_config(config: Dict) -> List[Tuple[str, str]]:
    """Extract trees list from config."""
    trees = []
    if 'trees' in config:
        for tree_config in config['trees']:
            if isinstance(tree_config, dict) and 'name' in tree_config and 'path' in tree_config:
                trees.append((tree_config['name'], tree_config['path']))
            else:
                raise ValueError(f"Invalid tree configuration: {tree_config}. Expected dict with 'name' and 'path' keys.")
    return trees

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
    elif 'trees' in config:
        trees_list = get_trees_from_config(config)
    else:
        raise ValueError("No trees specified. Use --trees argument or provide trees in config file.")
    
    # Create a dictionary of tree name to service
    trees = {}
    for name, tree_path in trees_list:
        # Resolve relative paths
        if args.config and not Path(tree_path).is_absolute():
            config_dir = Path(args.config).parent
            tree_path = str(config_dir / tree_path)
        
        repository = OpeningTreeRepository(tree_path)
        trees[name] = OpeningTreeService(repository)

    # Create and start the server
    protocol = 'http'  # Could be made configurable via args if needed
    domain = 'localhost'  # Could be made configurable via args if needed
    handler = create_handler(trees, port, protocol, domain)
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