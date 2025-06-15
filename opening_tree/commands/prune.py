from opening_tree.maintenance.pruning.tree_pruner import TreePruner

def prune_tree(args):
    """Prune single-game positions from the opening tree."""
    def progress_callback(stage: str, count: int):
        print(f"{stage}: {count} positions")

    pruner = TreePruner(args.tree)
    pruner.prune_single_game_positions(
        max_distance=args.max_closeness,
        batch_size=args.batch_size,
        progress_callback=progress_callback
    )