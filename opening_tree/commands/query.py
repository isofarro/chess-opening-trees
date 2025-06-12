from ..repository.database import OpeningTreeRepository
from ..service.opening_tree import OpeningTreeService
import json

def query_tree(args) -> None:
    """Query the opening tree for a specific position."""
    repository = OpeningTreeRepository(args.db)
    service = OpeningTreeService(repository)

    # Query the position through the service layer
    result = service.query_position(args.fen)
    if not result:
        print(f"Position not found: {args.fen}")
        return

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        # TODO: Implement other output formats if needed
        print(json.dumps(result, indent=2))