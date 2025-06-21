from typing import Optional, Callable

class GraphAnalyser:
    def __init__(self, repository):
        """Initialize the graph analyser.

        Args:
            repository: The pruning repository instance
        """
        self.repository = repository

    def calculate_closeness(
        self, max_steps: int = 5, batch_size: int = 1000,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ):
        """Calculate closeness to core positions (positions with more than one game)
        by traversing the move graph forward. Positions closer to core positions
        will have higher closeness values.

        Args:
            max_steps: Maximum steps away from core positions to consider
            batch_size: Number of positions to process in each batch
        """
        # First, identify positions directly reachable from core positions
        positions_updated = self.repository.mark_positions_near_core(max_steps)
        if progress_callback:
            progress_callback("Positions 1 step from core", positions_updated)
        if not positions_updated:
            return

        # Then propagate closeness values to positions reachable from those
        remaining_steps = max_steps - 1
        while remaining_steps > 0:
            positions_updated = self.repository.update_closeness_batch(remaining_steps)
            if progress_callback:
                progress_callback(f"Positions {max_steps - remaining_steps + 1} steps from core", positions_updated)
            if not positions_updated:
                break
            remaining_steps -= 1
