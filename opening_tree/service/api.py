from urllib.parse import unquote
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from opening_tree.repository.database import OpeningTreeRepository
from opening_tree.service.opening_tree import OpeningTreeService


class OpeningTreeAPI:
    """Core API logic for opening tree queries, usable by both HTTP server and WSGI."""
    
    def __init__(self, trees: Dict[str, OpeningTreeService], base_url: str = ""):
        self.trees = trees
        self.base_url = base_url
    
    def list_trees(self) -> Dict:
        """Get list of available trees."""
        tree_list = [{
            'name': name,
            'path': f'{self.base_url}/{name}/' if self.base_url else f'/{name}/'
        } for name in self.trees.keys()]
        return tree_list
    
    def query_position(self, tree_name: str, encoded_fen: str) -> Tuple[Optional[Dict], int, str]:
        """Query a position in a specific tree.
        
        Returns:
            Tuple of (result_data, status_code, error_message)
        """
        # Check if tree exists
        if tree_name not in self.trees:
            return None, 404, f"Tree '{tree_name}' not found"
        
        # Decode FEN from URL
        fen = unquote(encoded_fen)
        
        # Query the position
        result = self.trees[tree_name].query_position(fen)
        if not result:
            return None, 404, f"Position not found: {fen}"
        
        return result, 200, ""


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
            if isinstance(tree_config, dict) and 'name' in tree_config and 'file' in tree_config:
                trees.append((tree_config['name'], tree_config['file']))
            else:
                raise ValueError(f"Invalid tree configuration: {tree_config}. Expected dict with 'name' and 'file' keys.")
    return trees


def create_trees_from_config(config_path: str, trees_list: Optional[List[Tuple[str, str]]] = None) -> Dict[str, OpeningTreeService]:
    """Create tree services from config file or trees list.
    
    Args:
        config_path: Path to config file (used for relative path resolution)
        trees_list: Optional list of (name, path) tuples. If None, loads from config.
    
    Returns:
        Dictionary mapping tree names to OpeningTreeService instances
    """
    config = load_config(config_path) if config_path else {}
    
    if trees_list is None:
        trees_list = get_trees_from_config(config)
    
    if not trees_list:
        raise ValueError("No trees specified in config file or trees list.")
    
    # Create a dictionary of tree name to service
    trees = {}
    for name, tree_path in trees_list:
        # Resolve relative paths
        if config_path and not Path(tree_path).is_absolute():
            config_dir = Path(config_path).parent
            tree_path = str(config_dir / tree_path)
        
        repository = OpeningTreeRepository(tree_path)
        trees[name] = OpeningTreeService(repository)
    
    return trees