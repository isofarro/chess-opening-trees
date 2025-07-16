from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import os
from typing import Dict, Any, List

from opening_tree.service.api import OpeningTreeAPI, create_trees_from_config, load_config


# Global API instance
api: OpeningTreeAPI = None


def create_app(config_path: str = None) -> FastAPI:
    """Create FastAPI application with opening tree services.
    
    Args:
        config_path: Path to configuration file. If None, uses OPENING_TREE_CONFIG env var.
    """
    global api
    
    app = FastAPI(
        title="Opening Tree API",
        description="Chess opening tree analysis API",
        version="1.0.0"
    )
    
    # Determine config path
    if config_path is None:
        config_path = os.getenv('OPENING_TREE_CONFIG')
    
    if not config_path:
        raise ValueError("No config file specified. Set OPENING_TREE_CONFIG environment variable or pass config_path.")
    
    # Load configuration and create trees
    trees = create_trees_from_config(config_path)
    
    # Create API instance
    api = OpeningTreeAPI(trees)
    
    @app.get("/")
    async def list_trees(request: Request) -> List[Dict[str, Any]]:
        """List available opening trees."""
        # Construct base URL from request
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        
        # Create a temporary API instance with the correct base URL
        api_with_base_url = OpeningTreeAPI(api.trees, base_url)
        return api_with_base_url.list_trees()
    
    @app.get("/{tree_name}/{encoded_fen:path}")
    async def query_position(tree_name: str, encoded_fen: str) -> Dict[str, Any]:
        """Query a position in a specific opening tree.
        
        Args:
            tree_name: Name of the opening tree
            encoded_fen: URL-encoded FEN string of the position
        
        Returns:
            Position data with move statistics
        """
        result, status_code, error_message = api.query_position(tree_name, encoded_fen)
        
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=error_message)
        
        return result
    
    return app


# Create the WSGI application instance
# This will be used by uvicorn when running as: uvicorn opening_tree.wsgi:app
# Make sure to set OPENING_TREE_CONFIG environment variable
try:
    app = create_app()
except ValueError as e:
    # Create a placeholder app that shows the error
    app = FastAPI(title="Opening Tree API - Configuration Error")
    
    @app.get("/")
    async def config_error():
        return {
            "error": str(e),
            "message": "Set OPENING_TREE_CONFIG environment variable to point to your config file"
        }