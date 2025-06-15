from typing import Optional, Callable
from opening_tree.maintenance.pruning.workspace import PruningWorkspace
from opening_tree.maintenance.pruning.graph_analyser import GraphAnalyser
from opening_tree.maintenance.pruning.repository import PruningRepository
import sqlite3

class TreePruner:
    def __init__(self, main_tree_path: str, workspace_tree_path: Optional[str] = None):
        """Initialize the tree pruner.

        Args:
            main_tree_path: Path to the main opening tree database
            workspace_tree_path: Optional path for the temporary workspace database
        """
        self.main_tree_path = main_tree_path
        self.workspace_tree_path = workspace_tree_path or ':memory:'

    def prune_single_game_positions(self,
                                   max_distance: int = 5,
                                   batch_size: int = 1000,
                                   progress_callback: Optional[Callable[[str, int], None]] = None):
        conn = sqlite3.connect(self.workspace_tree_path)
        try:
            # Create repository and attach main database
            repository = PruningRepository(conn)
            repository.attach_main_database(self.main_tree_path)

            # Create workspace schema
            repository.create_schema()

            # Initialize workspace with single-game positions
            workspace = PruningWorkspace(repository)
            workspace.initialise_closeness()
            if progress_callback:
                count = self._count_positions(repository)
                progress_callback("Initialized workspace", count)

            # Calculate closeness to core positions
            analyser = GraphAnalyser(repository)
            analyser.calculate_closeness(max_distance, batch_size)
            if progress_callback:
                count = self._count_marked_positions(repository)
                progress_callback("Calculated position closeness", count)

            # Mark positions for deletion
            workspace.mark_positions_for_deletion(max_distance)
            if progress_callback:
                count = self._count_positions_to_delete(repository)
                progress_callback("Marked positions for deletion", count)

            # Delete positions in batches
            total_deleted = self._execute_batch_deletion(repository, batch_size, progress_callback)

            # Vacuum the database to reclaim space
            repository.vacuum_database()

            if progress_callback:
                progress_callback("Completed pruning", total_deleted)

        finally:
            if conn:
                repository.detach_main_database()
                conn.close()

    def _count_positions(self, repository: PruningRepository) -> int:
        """Count total positions being analyzed."""
        return repository.count_positions()

    def _count_marked_positions(self, repository: PruningRepository) -> int:
        """Count positions that have been processed."""
        return repository.count_marked_positions()

    def _count_positions_to_delete(self, repository: PruningRepository) -> int:
        """Count positions marked for deletion."""
        return repository.count_positions_to_delete()

    def _execute_batch_deletion(self,
                               repository: PruningRepository,
                               batch_size: int,
                               progress_callback: Optional[Callable[[str, int], None]] = None) -> int:
        """Execute the deletion of marked positions in batches, starting with leaf nodes.

        Returns:
            Total number of positions deleted
        """
        total_deleted = 0

        while True:
            # Try to get leaf positions first
            positions = repository.get_leaf_positions_for_deletion(batch_size)
            if not positions:
                # If no leaf positions left, get any remaining positions
                positions = repository.get_positions_for_deletion(batch_size)
                if not positions:
                    break

            repository.delete_positions(positions)
            batch_count = len(positions)
            total_deleted += batch_count

            if progress_callback:
                progress_callback("Deleting positions", total_deleted)

        return total_deleted