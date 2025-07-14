#!/usr/bin/env python3
"""
Script to run the Opening Tree API using uvicorn WSGI server.

Usage:
    python run_wsgi.py --config config.json --port 8000
    
Or set environment variable:
    export OPENING_TREE_CONFIG=config.json
    python run_wsgi.py --port 8000
"""

import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run Opening Tree API with uvicorn"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file (JSON format)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    # Set config environment variable if provided
    if args.config:
        config_path = Path(args.config).resolve()
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}")
            sys.exit(1)
        os.environ['OPENING_TREE_CONFIG'] = str(config_path)
    
    # Check if config is set
    if not os.getenv('OPENING_TREE_CONFIG'):
        print("Error: No configuration file specified.")
        print("Use --config argument or set OPENING_TREE_CONFIG environment variable.")
        sys.exit(1)
    
    # Import and run uvicorn
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn not installed. Run: pip install uvicorn")
        sys.exit(1)
    
    print(f"Starting Opening Tree API on {args.host}:{args.port}")
    print(f"Using config: {os.getenv('OPENING_TREE_CONFIG')}")
    
    # Configure uvicorn for optimal performance
    uvicorn_config = {
        "app": "opening_tree.wsgi:app",
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "access_log": False,  # Disable access logging for performance
        "workers": 1,  # Single worker for SQLite (no shared state)
    }
    
    # Add performance optimizations if available
    try:
        import uvloop
        uvicorn_config["loop"] = "uvloop"  # Faster event loop
    except ImportError:
        pass
    
    try:
        import httptools
        uvicorn_config["http"] = "httptools"  # Faster HTTP parser
    except ImportError:
        pass
    
    uvicorn.run(**uvicorn_config)

if __name__ == "__main__":
    main()